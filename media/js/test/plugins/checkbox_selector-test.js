require(['plugins/checkbox_selector', 'libs/jquery'], function (CheckboxSelector) {
    buster.testCase("Checkbox Selector", {
        setUp: function () {
            this.table = $('<table><tr><th id="select"></th></tr><tr><td><input type="checkbox" class="selector" /><input type="checkbox" class="selector" /></td></tr></table>');
            $('body').append(this.table);
            this.cs = new CheckboxSelector($("#select", this.table), '.selector');
            this.cs.add();
        },
        "should create a checkbox in the node": function () {
            assert.equals($('#select input[type=checkbox]').length, 1);
        },
        "should toggle on all the other checkboxes based on main one": function () {
            // Need to click twice, no idea why
            $('#select input[type=checkbox]').click();
            $('#select input[type=checkbox]').click();
            var toggled = 0;
            $('.selector').each(function () {
                if ($(this).attr('checked') == 'checked') {
                    toggled++;
                }
            });
            assert.equals(toggled, 2);
        }
    });
});
