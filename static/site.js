var Site = {
    init : function() {
        this.subscriptionEvents();
    },

    subscriptionEvents : function () {
        $("a.subscription").on("click", function () {
            var volume = $(this);
            function toggleSubscription() {
                volume.find("span.glyphicon").toggleClass(
                    "glyphicon-heart glyphicon-heart-empty");
                if(volume.data("subscribed") == "True") {
                    volume.data("subscribed", "False");
                } else {
                    volume.data("subscribed", "True");
                }
            };
            if(volume.data("subscribed") == "True") {
                console.log('unsubscribing...');
                $.ajax({
                    url: '/subscriptions/remove/' + volume.data("volume") +
                        '?type=ajax',
                    success: toggleSubscription,
                });
            } else {
                console.log('subscribing...');
                $.ajax({
                    url: '/subscriptions/add/' + volume.data("volume") +
                        '?type=ajax',
                    success: toggleSubscription,
                });
            }
        });
    },
};

$(document).ready( function() {
    Site.init();
});
