
// forum utils

$(document).ready(function(){
    $(".account_info_trigger").click(function(e){
        console.log("clicked");
        e.preventDefault();

        // open account dialog
        $(".account_info_dialog").toggle();
        $(this).toggleClass("active");
    });
});
