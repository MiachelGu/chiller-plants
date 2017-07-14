var dashboard = new Dashboard();

dashboard.addWidget('MyWidget', 'Number', {
    getData: function () {
        var self = this;
        Dashing.utils.get('my_widget', function(data) {
            console.log(data);
            $.extend(self.scope, data);
        });
    },
    interval: 3000
});