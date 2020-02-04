$(document).ready(function() {
    'use strict'

    // CSRF
    var csrftoken = $.cookie('csrftoken');
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    // Invest num shares input buttons
    function get_num_shares() {
        var value = $('.invest-num-shares > input').val();
        if (!$.isNumeric(value)) value = 1;
        return parseInt(value);
    }
    function num_shares_updated() {
        // Enforce minimum and maximum
        var num_shares = get_num_shares();
        num_shares = Math.max(1, num_shares);
        num_shares = Math.min(num_shares, num_shares_remaining);

        // Set num shares in input
        $('.invest-num-shares > input').val(num_shares);

        // Disable minus button when only 1 share
        if (num_shares === 1) {
            $('.invest-num-shares > button#remove-shares').addClass('disabled').prop('disabled', true);
        } else {
            $('.invest-num-shares > button#remove-shares').removeClass('disabled').prop('disabled', false);
        }
        // Disable plus button when max shares
        if (num_shares === num_shares_remaining) {
            $('.invest-num-shares > button#add-shares').addClass('disabled').prop('disabled', true);
        } else {
            $('.invest-num-shares > button#add-shares').removeClass('disabled').prop('disabled', false);
        }

        // Update invest button text
        var subtotal_cost_cents = get_subtotal_cost_cents();
        var subtotal_shares_price = parseFloat(subtotal_cost_cents / 100).toFixed(2);
        var button_text = "Invest $" + subtotal_shares_price;
        $('button#invest-button').text(button_text);

        // Update shares price
        var fees_cost_cents = get_fees_cost_cents();
        $('#subtotal-shares-price').text("$" + subtotal_shares_price + " + ");
        var fees_price = parseFloat(fees_cost_cents / 100).toFixed(2);
        $('#fees-price').text("$" + fees_price);
        var total_shares_price = parseFloat((subtotal_cost_cents + fees_cost_cents) / 100).toFixed(2);
        $('#shares-price').text(" $" + total_shares_price);
    }
    $('.invest-num-shares > input').change(function() {
        num_shares_updated();
    });
    if (typeof num_shares_remaining != 'undefined') num_shares_updated();

    // Press buttons to update shares
    $('.invest-num-shares > button').click(function() {
        // Get the current number of shares
        var num_shares = get_num_shares();

        // Decrement or increment number of shares based on button pressed
        if ($(this).is('.invest-num-shares > button#remove-shares')) {
            num_shares -= 1;
        } else if ($(this).is('.invest-num-shares > button#add-shares')) {
            num_shares += 1;
        } else {
            console.log("Unexpected invest-num-shares button pressed.");
        }
        $('.invest-num-shares > input').val(num_shares);
        num_shares_updated();
    });

    // Cost for shares
    function get_subtotal_cost_cents() {
        return get_num_shares() * share_value_cents;
    }
    function get_fees_cost_cents() {
        var subtotal = get_num_shares() * share_value_cents;
        var stripe_flat_fee_cents = stripe_flat_fee * 100;
        var transaction_fees = subtotal * (perdiem_percentage + stripe_percentage) + stripe_flat_fee_cents;
        return Math.ceil(transaction_fees);
    }
    function get_total_cost_cents() {
        return get_subtotal_cost_cents() + get_fees_cost_cents();
    }

    // Click Invest button
    function click_invest() {
        stripe_handler.open({
            name: 'PerDiem',
            description: 'Invest in ' + artist_name,
            amount: get_total_cost_cents()
        });
    }
    $('#invest-button').click(function(e) {
        click_invest();
        e.preventDefault();
    });
    $('.invest-num-shares > input').keydown(function(e) {
        if (e.keyCode == 10 | e.keyCode == 13) {
            click_invest();
            e.preventDefault();
        }
    });

    $(window).on('popstate', function() {
        handler.close();
    });

    // Delete Update
    $('button.delete-update').click(function() {
        var selectorId = $(this).attr('id');
        var update_id = parseInt(selectorId.split("-")[1]);
        var url = "/api/update/" + update_id + "/?format=json";
        $.ajax({
            url: url,
            type: 'DELETE',
            contentType: 'application/json'
        }).done(function() {
            // Delete update
            $('ul.updates > li#' + selectorId).remove();
        });
    });
});
