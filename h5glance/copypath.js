// Based on code by Stackoverflow user Dean Taylor
// https://stackoverflow.com/questions/400212/how-do-i-copy-to-the-clipboard-in-javascript/30810322
// Used under Stackoverflow's CC-BY-SA 3.0 license

(function() {
    function copyTextToClipboard(text) {
        let textArea = document.createElement("textarea");

        //
        // *** This styling is an extra step which is likely not required. ***
        //
        // Why is it here? To ensure:
        // 1. the element is able to have focus and selection.
        // 2. if element was to flash render it has minimal visual impact.
        // 3. less flakyness with selection and copying which **might** occur if
        //    the textarea element is not visible.
        //
        // The likelihood is the element won't even render, not even a flash,
        // so some of these are just precautions. However in IE the element
        // is visible whilst the popup box asking the user for permission for
        // the web page to copy to the clipboard.
        //

        // Place in top-left corner of screen regardless of scroll position.
        textArea.style.position = 'fixed';
        textArea.style.top = 0;
        textArea.style.left = 0;

        // Ensure it has a small width and height. Setting to 1px / 1em
        // doesn't work as this gives a negative w/h on some browsers.
        textArea.style.width = '2em';
        textArea.style.height = '2em';

        // We don't need padding, reducing the size if it does flash render.
        textArea.style.padding = 0;

        // Clean up any borders.
        textArea.style.border = 'none';
        textArea.style.outline = 'none';
        textArea.style.boxShadow = 'none';

        // Avoid flash of white box if rendered for any reason.
        textArea.style.background = 'transparent';


        textArea.value = text;

        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            if (!document.execCommand('copy')) {
                console.log("Unable to copy text with document.execCommand()");
            }
        } finally {
            document.body.removeChild(textArea);
        }
    }

    function copy_event_handler(event) {
        copyTextToClipboard(event.target.dataset.hdf5Path);
        event.preventDefault();
    }

    function enable_copylinks(parent) {
        let links = parent.querySelectorAll(".h5glance-dataset-copylink");
        links.forEach(function (link) {
            link.addEventListener("click", copy_event_handler);
        });
    }

    // The code to actually trigger this is substituted below.
    //ACTIVATE
})();
