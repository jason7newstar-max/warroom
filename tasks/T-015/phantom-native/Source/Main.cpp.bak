// PHANTOM — native low-latency monitor engine (JUCE), v2.
// Real-time CLA-style vocal chain at a 64-sample buffer (~2.7 ms round-trip on a Duet).
// v2 adds: 5 switchable Vocal-Chain TEMPLATES + a tiny file control-bridge so the
// PHANTOM web UI can drive it (monitor on/off, pick template) live.
//
// Control bridge (plain key=value files, no deps):
//   reads  ~/.phantom/control.txt   -> "monitor=1\npreset=2\n"
//   writes ~/.phantom/status.txt    -> "callbacks=..\npeak=..\nmonitor=..\npreset=..\nname=.."
//
// Build: see README.md.  Run: ./build/PhantomNative_artefacts/Release/PhantomNative

#include <juce_audio_devices/juce_audio_devices.h>
#include <juce_audio_formats/juce_audio_formats.h>
#include <juce_dsp/juce_dsp.h>
#include <iostream>
#include <atomic>
#include <cmath>
#include <memory>
#include <vector>

using namespace juce;

static std::atomic<long> g_callbacks { 0 };
static std::atomic<float> g_peakDb { -90.0f };

// ---- 5 Vocal-Chain templates ----
struct Preset
{
    String name;
    float hpHz;
    float compThresh, compRatio, compAtt, compRel;
    float deMudHz, deMudGain;          // peak EQ (gain in dB; 0 = off)
    float presHz, presGain, presQ;     // presence peak EQ
    float airHz, airGain;              // high shelf (dB; can be negative to roll off)
    float lowHz, lowGain;              // low shelf warmth (dB)
    float driveDb;                     // tanh saturation pre-gain (0 = clean)
    float makeupDb;
    float revRoom, revWet, revDamp;
    float delayMs, delayFb, delayMix;  // slap/echo before the reverb (mix 0 = off)
};

static const Preset DEFAULT_PRESETS[5] = {
    // name           hp    comp(thr ratio att rel)  deMud(hz g)  pres(hz g q)   air(hz g)   low(hz g)  drive makeup  rev(room wet damp)  delay(ms fb mix)
    { "POP SHEEN",    90,  -22, 4.0f, 3,   80,        350, -2.0f,  4000, 3.0f,1.2f, 8000, 3.5f,    0,   0.0f,  0,    3.0f,  0.50f,0.14f,0.40f,  0,    0.0f, 0.0f },
    { "RAP UPFRONT", 100,  -24, 6.0f, 2,   60,        300, -2.5f,  3000, 4.0f,1.0f, 9000, 2.5f,    0,   0.0f,  3.0f, 4.0f,  0.12f,0.05f,0.50f,  110,  0.12f,0.10f },
    { "R&B SILK",     80,  -20, 3.0f, 8,  120,          0,  0.0f,  5000, 2.0f,1.5f,10000, 3.0f,  200,   2.0f,  0,    2.0f,  0.65f,0.24f,0.30f,  180,  0.20f,0.12f },
    { "STAGE BIG",    90,  -22, 4.0f, 3,   80,        350, -1.5f,  4000, 3.0f,1.2f, 8000, 3.0f,    0,   0.0f,  0,    3.0f,  0.85f,0.30f,0.20f,  0,    0.0f, 0.0f },
    { "VINTAGE WARM",120,  -18, 3.0f,10,  140,          0,  0.0f,  2500, 2.0f,1.0f, 9000,-3.0f,  180,   3.0f,  6.0f, 2.0f,  0.25f,0.10f,0.60f,  200,  0.15f,0.08f },
};

// The ACTIVE preset bank — loaded from ~/.phantom/presets.txt (the generator writes it);
// falls back to the 5 defaults above. Hot-reloaded when the file changes.
static std::vector<Preset> g_presets;

static File presetsFile() { return File::getSpecialLocation (File::userHomeDirectory).getChildFile (".phantom/presets.txt"); }

static void loadPresets()
{
    std::vector<Preset> v;
    auto f = presetsFile();
    if (f.existsAsFile())
    {
        for (auto& line : StringArray::fromLines (f.loadFileAsString()))
        {
            if (line.trim().isEmpty() || line.trim().startsWith ("#")) continue;
            auto t = StringArray::fromTokens (line, "|", "");
            if (t.size() < 23) continue;
            Preset p; p.name = t[0].trim();
            float* fld[22] = { &p.hpHz,&p.compThresh,&p.compRatio,&p.compAtt,&p.compRel,
                               &p.deMudHz,&p.deMudGain,&p.presHz,&p.presGain,&p.presQ,
                               &p.airHz,&p.airGain,&p.lowHz,&p.lowGain,&p.driveDb,&p.makeupDb,
                               &p.revRoom,&p.revWet,&p.revDamp,&p.delayMs,&p.delayFb,&p.delayMix };
            for (int i = 0; i < 22; ++i) *fld[i] = t[i + 1].getFloatValue();
            v.push_back (p);
        }
    }
    if (v.empty())
        for (auto& d : DEFAULT_PRESETS) v.push_back (d);
    g_presets = std::move (v);
}

class VocalMonitor : public AudioIODeviceCallback
{
public:
    std::atomic<int>  preset { 0 };
    std::atomic<bool> monitorOn { true };
    std::atomic<bool> recording { false };   // capture DRY input to disk (record dry, monitor wet)
    std::atomic<bool> dirty { false };       // set when the preset bank is hot-reloaded

    void audioDeviceAboutToStart (AudioIODevice* device) override
    {
        sampleRate = device->getCurrentSampleRate();
        spec = { sampleRate, (uint32) device->getCurrentBufferSizeSamples(), 1 };
        hpf.prepare (spec); comp.prepare (spec); deMud.prepare (spec);
        presence.prepare (spec); air.prepare (spec); lowShelf.prepare (spec);
        drive.prepare (spec); reverb.setSampleRate (sampleRate);
        delayLine.prepare (spec); delayLine.reset();
        drive.functionToUse = [] (float x) { return std::tanh (x); };
        recRing.setSize (1, RING); recFifo.reset();
        applyPreset (preset.load());
        applied = preset.load();
    }

    // drained from the control thread into a WAV writer
    int drain (AudioBuffer<float>& out)
    {
        const int ready = recFifo.getNumReady();
        int s1, n1, s2, n2; recFifo.prepareToRead (ready, s1, n1, s2, n2);
        int n = 0;
        if (n1 > 0) { out.copyFrom (0, 0, recRing, 0, s1, n1); n += n1; }
        if (n2 > 0) { out.copyFrom (0, n, recRing, 0, s2, n2); n += n2; }
        recFifo.finishedRead (n1 + n2);
        return n;
    }

    void audioDeviceStopped() override {}

    void applyPreset (int idx)
    {
        if (g_presets.empty()) return;
        const auto& p = g_presets[(size_t) jlimit (0, (int) g_presets.size() - 1, idx)];
        hpf.coefficients = dsp::IIR::Coefficients<float>::makeHighPass (sampleRate, p.hpHz);
        comp.setThreshold (p.compThresh); comp.setRatio (p.compRatio);
        comp.setAttack (p.compAtt); comp.setRelease (p.compRel);
        deMud.coefficients    = dsp::IIR::Coefficients<float>::makePeakFilter (sampleRate, p.deMudHz > 0 ? p.deMudHz : 1000.0f, 1.0f, Decibels::decibelsToGain (p.deMudGain));
        presence.coefficients = dsp::IIR::Coefficients<float>::makePeakFilter (sampleRate, p.presHz, p.presQ, Decibels::decibelsToGain (p.presGain));
        air.coefficients      = dsp::IIR::Coefficients<float>::makeHighShelf (sampleRate, p.airHz, 0.7f, Decibels::decibelsToGain (p.airGain));
        lowShelf.coefficients = dsp::IIR::Coefficients<float>::makeLowShelf (sampleRate, p.lowHz > 0 ? p.lowHz : 200.0f, 0.7f, Decibels::decibelsToGain (p.lowGain));
        preGain = Decibels::decibelsToGain (p.driveDb);
        useDrive = p.driveDb > 0.1f;
        makeup = Decibels::decibelsToGain (p.makeupDb);
        Reverb::Parameters rp; rp.roomSize = p.revRoom; rp.wetLevel = p.revWet; rp.dryLevel = 1.0f - p.revWet * 0.5f; rp.damping = p.revDamp; rp.width = 1.0f;
        reverb.setParameters (rp);
        dlySamps = jlimit (1, 95000, (int) (p.delayMs / 1000.0f * (float) sampleRate));
        dlyFb = jlimit (0.0f, 0.9f, p.delayFb); dlyMix = jlimit (0.0f, 1.0f, p.delayMix);
        delayLine.setDelay ((float) dlySamps);
    }

    void audioDeviceIOCallbackWithContext (const float* const* in, int numIn,
                                           float* const* out, int numOut,
                                           int numSamples, const AudioIODeviceCallbackContext&) override
    {
        g_callbacks.fetch_add (1);
        const int want = preset.load();
        if (want != applied || dirty.exchange (false)) { applyPreset (want); applied = want; }

        AudioBuffer<float> buf (1, numSamples);
        if (numIn > 0 && in[0] != nullptr) buf.copyFrom (0, 0, in[0], numSamples); else buf.clear();
        g_peakDb.store (Decibels::gainToDecibels (buf.getMagnitude (0, numSamples)));

        // capture the DRY input (before any monitor processing) -> lock-free FIFO
        if (recording.load())
        {
            int s1, n1, s2, n2; recFifo.prepareToWrite (numSamples, s1, n1, s2, n2);
            if (n1 > 0) recRing.copyFrom (0, s1, buf.getReadPointer (0), n1);
            if (n2 > 0) recRing.copyFrom (0, s2, buf.getReadPointer (0) + n1, n2);
            recFifo.finishedWrite (n1 + n2);
        }

        if (monitorOn.load())
        {
            dsp::AudioBlock<float> blk (buf);
            dsp::ProcessContextReplacing<float> ctx (blk);
            hpf.process (ctx); comp.process (ctx); deMud.process (ctx);
            presence.process (ctx); air.process (ctx); lowShelf.process (ctx);
            if (useDrive) { buf.applyGain (preGain); drive.process (ctx); }
            buf.applyGain (makeup);
            if (dlyMix > 0.0f)                              // slap / echo before the reverb
            {
                auto* d = buf.getWritePointer (0);
                for (int n = 0; n < numSamples; ++n)
                {
                    float in = d[n];
                    float wet = delayLine.popSample (0);
                    delayLine.pushSample (0, in + wet * dlyFb);
                    d[n] = in + wet * dlyMix;
                }
            }
            reverb.processMono (buf.getWritePointer (0), numSamples);
            for (int ch = 0; ch < numOut; ++ch) if (out[ch]) FloatVectorOperations::copy (out[ch], buf.getReadPointer (0), numSamples);
        }
        else
            for (int ch = 0; ch < numOut; ++ch) if (out[ch]) FloatVectorOperations::clear (out[ch], numSamples);
    }

private:
    double sampleRate = 48000.0;
    dsp::ProcessSpec spec {};
    int   applied = -1;
    float preGain = 1.0f, makeup = 1.0f; bool useDrive = false;
    dsp::IIR::Filter<float> hpf, deMud, presence, air, lowShelf;
    dsp::Compressor<float>  comp;
    dsp::WaveShaper<float>  drive;
    dsp::DelayLine<float, dsp::DelayLineInterpolationTypes::Linear> delayLine { 96000 };
    int dlySamps = 1; float dlyFb = 0.0f, dlyMix = 0.0f;
    Reverb reverb;
    static constexpr int RING = 48000 * 30;   // 30 s ring, drained continuously
    AbstractFifo recFifo { RING };
    AudioBuffer<float> recRing;
};

static File controlFile() { return File::getSpecialLocation (File::userHomeDirectory).getChildFile (".phantom/control.txt"); }
static File statusFile()  { return File::getSpecialLocation (File::userHomeDirectory).getChildFile (".phantom/status.txt"); }
static File takesDir()    { return File::getSpecialLocation (File::userHomeDirectory).getChildFile ("claude-work/warroom/tasks/T-015/recorder/studio_ui/takes"); }

int main()
{
    AudioDeviceManager dm;
    dm.initialiseWithDefaultDevices (1, 2);
    String duet;
    for (auto* t : dm.getAvailableDeviceTypes()) { t->scanForDevices(); for (auto& n : t->getDeviceNames (true)) if (n.containsIgnoreCase ("duet")) duet = n; }

    auto setup = dm.getAudioDeviceSetup();
    setup.bufferSize = 64; setup.sampleRate = 48000.0;
    if (duet.isNotEmpty()) { setup.inputDeviceName = duet; setup.outputDeviceName = duet; }
    setup.useDefaultInputChannels = true; setup.useDefaultOutputChannels = true;
    auto err = dm.setAudioDeviceSetup (setup, true);
    if (err.isNotEmpty()) std::cout << "SETUP ERROR: " << err << std::endl;

    loadPresets();
    int64 presetsMtime = presetsFile().getLastModificationTime().toMilliseconds();

    VocalMonitor monitor;
    dm.addAudioCallback (&monitor);

    if (auto* dev = dm.getCurrentAudioDevice())
        std::cout << "PHANTOM native · " << dev->getName() << " · buffer=" << dev->getCurrentBufferSizeSamples()
                  << " · round-trip ~" << (2.0 * dev->getCurrentBufferSizeSamples() / dev->getCurrentSampleRate() * 1000.0)
                  << " ms · " << "5 templates, web-controlled" << std::endl;
    else std::cout << "NO DEVICE OPENED" << std::endl;
    std::cout.flush();

    controlFile().create();
    takesDir().createDirectory();
    std::unique_ptr<AudioFormatWriter> writer;
    AudioBuffer<float> drainBuf (1, 48000 * 30);
    bool wasRec = false;
    String lastTake;

    for (;;)
    {
        Thread::sleep (50);
        // hot-reload the preset bank if the generator rewrote it
        const int64 mt = presetsFile().getLastModificationTime().toMilliseconds();
        if (mt != presetsMtime) { presetsMtime = mt; loadPresets(); monitor.dirty.store (true); }
        const int nPresets = jmax (1, (int) g_presets.size());
        // read control
        auto txt = controlFile().loadFileAsString();
        for (auto& line : StringArray::fromLines (txt))
        {
            if (line.startsWith ("monitor=")) monitor.monitorOn.store (line.fromFirstOccurrenceOf ("=", false, false).getIntValue() != 0);
            if (line.startsWith ("preset="))  { int p = jlimit (0, nPresets - 1, line.fromFirstOccurrenceOf ("=", false, false).getIntValue()); monitor.preset.store (p); }
            if (line.startsWith ("record="))  monitor.recording.store (line.fromFirstOccurrenceOf ("=", false, false).getIntValue() != 0);
        }

        // recording: record dry, monitor wet
        const bool rec = monitor.recording.load();
        if (rec && ! wasRec)                       // start
        {
            auto f = takesDir().getChildFile ("take-" + Time::getCurrentTime().formatted ("%H%M%S") + ".wav");
            f.deleteFile();
            if (auto fos = f.createOutputStream())
            {
                WavAudioFormat wav;
                writer.reset (wav.createWriterFor (fos.get(), 48000.0, 1, 16, {}, 0));
                if (writer != nullptr) { fos.release(); lastTake = f.getFileName(); }
            }
        }
        if (rec && writer != nullptr)              // drain dry -> disk
        {
            int n = monitor.drain (drainBuf);
            if (n > 0) writer->writeFromAudioSampleBuffer (drainBuf, 0, n);
        }
        if (! rec && wasRec) writer.reset();       // stop = flush + close
        wasRec = rec;

        // write status
        String s;
        s << "callbacks=" << (int) g_callbacks.load() << "\n"
          << "peak=" << String (g_peakDb.load(), 1) << "\n"
          << "monitor=" << (monitor.monitorOn.load() ? 1 : 0) << "\n"
          << "preset=" << monitor.preset.load() << "\n"
          << "count=" << nPresets << "\n"
          << "name=" << g_presets[(size_t) jlimit (0, nPresets - 1, monitor.preset.load())].name << "\n"
          << "recording=" << (rec ? 1 : 0) << "\n"
          << "last_take=" << lastTake << "\n";
        statusFile().replaceWithText (s);
    }
    return 0;
}
