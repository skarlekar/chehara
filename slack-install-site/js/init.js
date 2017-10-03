(function($){
  $(function(){
    $('.modal').modal();

    const locationParts = window.location.href.split('#');

    if (locationParts.length > 1) {
      const fragment = locationParts[1];
      if (fragment === 'success') $('#successModal').modal('open');
      if (fragment === 'error') $('#errorModal').modal('open');
    }
  }); // end of document ready
})(jQuery); // end of jQuery name space
