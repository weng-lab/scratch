function updateTissues(){
    $(".selectTissues").hide();

    var assembly = "hg19";
    if($("#assembly_mm9").is(":checked")){
        assembly = "mm9";
    } else if($("#assembly_mm10").is(":checked")){
        assembly = "mm10";
    }

    var assays = "H3K27ac";
    if($("#assaysBoth").is(":checked")){
        assays = "Both";
    } else if($("#assaysDNase").is(":checked")){
        assays = "DNase";
    }

    $("#content" + assembly + assays).show();

    // http://stackoverflow.com/a/8579673
    var aTag = $("a[href='#search']");
    $('html,body').animate({scrollTop: aTag.offset().top},
                           1400,
                           "easeOutQuint");
}

function selectAllNone(setChecked){
    // filter performance note by https://api.jquery.com/hidden-selector/
    $(".selectTissues").filter(":visible")
        .find(":checkbox").prop('checked', setChecked);
}

function select(devPt){
    $(".selectTissues").filter(":visible")
        .find("*[value*='" + devPt + "']")
        .prop('checked',
              function( i, val ) {
                  return !val;
              });
}

$(document).ready(function(){
    // http://stackoverflow.com/a/28603203
    $("#selectAssays :input").change(function() {
        updateTissues();
    });

    $("#selectAssembly :input").change(function() {
        updateTissues();
    });

    $("#selectAll").on('click', function(e){ e.preventDefault(); selectAllNone(true); });
    $("#selectNone").on('click', function(e){ e.preventDefault(); selectAllNone(false); });
    $("#select115").on('click', function(e){ e.preventDefault(); select("11.5"); });
    $("#select135").on('click', function(e){ e.preventDefault(); select("13.5"); });
    $("#select145").on('click', function(e){ e.preventDefault(); select("14.5"); });
    $("#select155").on('click', function(e){ e.preventDefault(); select("15.5"); });
    $("#select165").on('click', function(e){ e.preventDefault(); select("16.5"); });
    $("#selectp0").on('click', function(e){ e.preventDefault(); select("postnatal_0"); });

    $.each(["mm9", "mm10", "hg19"], function(assemblyIdx, assembly){
        $.each(["Both", "H3K27ac", "DNase"], function(assayIdx, assays){
            var dom = "table" + assembly + assays;
            //$(dom).DataTable();
        });
    });
})

