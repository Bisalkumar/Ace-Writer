$(document).ready(function () {

    $('.carousel').owlCarousel({
        margin: 40,
        loop: true,
        autoplay: true,
        autoplayTimeOut: 7000,
        autoplayHoverPause: true,
        responsive: {
            0: {
                items: 1,
                nav: false
            },
            600: {
                items: 2,
                nav: false
            },
            1000: {
                items: 3,
                nav: false
            }
        }
    });
});