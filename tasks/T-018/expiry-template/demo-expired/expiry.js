(function () {
  var config = window.ONE_TEN_PREVIEW || {};
  var deployedAt = new Date(config.deployedAt);
  var days = Number(config.expiresAfterDays || 7);

  if (!config.deployedAt || Number.isNaN(deployedAt.getTime())) {
    return;
  }

  var expiresAt = deployedAt.getTime() + days * 24 * 60 * 60 * 1000;

  if (Date.now() <= expiresAt) {
    return;
  }

  var template = document.getElementById("expired-template");
  if (!template) {
    return;
  }

  document.body.replaceChildren(template.content.cloneNode(true));
  document.documentElement.classList.add("is-expired");
})();
