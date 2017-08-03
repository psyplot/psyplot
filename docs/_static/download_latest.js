
function GetLatestReleaseInfo(osname) {
    $.getJSON("https://api.github.com/repos/Chilipp/psyplot-conda/releases/latest").done(function (release) {
        var asset = release.assets[0];
        for (var i = 0; i < release.assets.length; i++) {
            if (release.assets[i].name.includes(osname))
            {
                var asset = release.assets[i];
            }
        }
        window.location.replace(asset.browser_download_url);
    });
}
