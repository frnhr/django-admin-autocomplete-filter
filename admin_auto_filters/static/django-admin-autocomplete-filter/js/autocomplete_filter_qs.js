django.jQuery(document).ready(function ($) {

    function search_replace(name, value) {
        var new_search_hash = search_to_hash();
        new_search_hash[decodeURIComponent(name)] = [];
        new_search_hash[decodeURIComponent(name)].push(decodeURIComponent(value));
        return hash_to_search(new_search_hash);
      }

    function search_remove(name, value) {
        var new_search_hash = search_to_hash();
        if (new_search_hash[name].indexOf(value) >= 0) {
          new_search_hash[name].splice(new_search_hash[name].indexOf(value), 1);
          if (new_search_hash[name].length == 0) {
            delete new_search_hash[name];
          }
        }
        return hash_to_search(new_search_hash);
    }

    function search_to_hash() {
        var h={};
        if (window.location.search == undefined || window.location.search.length < 1) { return h;}
        q = window.location.search.slice(1).split('&');
        for (var i = 0; i < q.length; i++) {
          var key_val = q[i].split('=');
          // replace '+' (alt space) char explicitly since decode does not
          var hkey = decodeURIComponent(key_val[0]).replace(/\+/g,' ');
          var hval = decodeURIComponent(key_val[1]).replace(/\+/g,' ');
          if (h[hkey] == undefined) {
            h[hkey] = [];
          }
          h[hkey].push(hval);
        }
        return h;
    }

    function hash_to_search(h) {
        var search = String("?");
        for (var k in h) {
          for (var i = 0; i < h[k].length; i++) {
            search += search == "?" ? "" : "&";
            search += encodeURIComponent(k) + "=" + encodeURIComponent(h[k][i]);
          }
        }
        return search;
    }

    var $changelistSidebar = $('#changelist-filter');
    var autocompleteInitialVal = $changelistSidebar.data('autocompleteInitialVal');

    if (autocompleteInitialVal) return;
    autocompleteInitialVal = {};
    $changelistSidebar.data('autocompleteInitialVal', autocompleteInitialVal);

    $changelistSidebar.find('select.admin-autocomplete').each(function() {
       autocompleteInitialVal[this.name] = $(this).val();
    });

    var observer = new MutationObserver(function() {
        var $selects = $changelistSidebar.find('select.admin-autocomplete');
        $selects.each(function () {
            let $select = $(this);
            var val = $select.val();
            var oldVal = $changelistSidebar.data('autocompleteInitialVal')[$select[0].name];
            if (val !== oldVal) {
                if (val) {
                    window.location.search = search_replace($select[0].name, val);
                } else {
                    window.location.search = search_remove($select[0].name, oldVal);
                }
            }
        });
    });
    observer.observe($changelistSidebar[0], { attributes: false, childList: true, subtree: true });
});
