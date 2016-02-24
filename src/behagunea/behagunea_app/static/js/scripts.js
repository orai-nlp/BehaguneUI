function show_all_tweets(type) {
  $('#loading_modal').modal('show');
  $.ajax({
    method: 'GET',
    url: '/behagunea/reload_tweets',
    dataType: 'html',
    data: {
      category: $('#id_category').val(),
      tag: $('#id_tag').val(),
      user: $('#id_user').val(),
      date: $('#id_date').val(),
      lang: $('#id_lang').val(),
      type: $('#id_type').val(),
      influence: $('#id_influence').val(),
      source: $('#id_source').val(),
      polarity: type
    }
  }).done(function (data) {
    var new_row = $(data);
    //$("#row_2").html(new_row);                 
    $('#loading_modal').modal('hide');
    $('#modal_tweets').html(new_row);
    $('#modal_tweets').modal('show');
    return false;
  });
}
function show_all_tweets_pagination(type, page) {
  var order = $('a.selected').attr('id');
  var ord_dir;
  if ($('a.selected').hasClass('asc'))
  ord_dir = 'asc' 
  else
  ord_dir = 'desc'
  $('#loading_modal').modal('show');
  $.ajax({
    method: 'GET',
    url: '/behagunea/reload_tweets',
    dataType: 'html',
    data: {
      category: $('#id_category').val(),
      tag: $('#id_tag').val(),
      user: $('#id_user').val(),
      date: $('#id_date').val(),
      lang: $('#id_lang').val(),
      type: $('#id_type').val(),
      influence: $('#id_influence').val(),
      source: $('#id_source').val(),
      polarity: type,
      page: page,
      order: order,
      ord_dir: ord_dir
    }
  }).done(function (data) {
    var new_row = $(data);
    //$("#row_2").html(new_row);                 
    $('#loading_modal').modal('hide');
    $('#modal_tweets').html(new_row);
    $('#modal_tweets').modal('show');
    return false;
  });
};
$('.close').click(function () {
  $(this).parent().hide();
});
$('#tag_cloud .minimize_maximize').click(function () {
  $('#row_1').slideToggle(500);
  var img = $(this).find('img');
  var containers = $(".svg-container svg");
  if ($(img).attr('src') == '/static/img/maximize.png') {
    img.attr('src', '/static/img/minimize.png');
    if ($('#row_2').css('display') != 'none') { // irekia dago tweetena
      w = global_w;
      h = w/3.8;
      $(containers).each(function(){
        //$(this)[0].setAttribute('viewBox', '0 0 '+ w +' '+ h );
        $(this).attr("width", w).attr("height", h);
      });
      if ($('a[name=\'cloud_selector\'].active').attr('id') == 'selector_egileak') { // egileak erakutsi behar dira
        $('#tagCloud').hide();
        $('#sourceTagCloud').show();
      } 
      else {
        // etiketak erakutsi behar dira
        $('#tagCloud').show();
        $('#sourceTagCloud').hide();
      }
      // Adapt main div's padding:
      var div=$('#row_1 .percent_30');
      if ($(div).hasClass("big_size"))
          $(div).attr("class",$(div).attr("class").replace("big_size",""));
          
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_pie') {
        $('#pieChart').show();
        $('#countChart').hide();
        $('#timeChart').hide();
      }
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_time') {
        $('#pieChart').hide();
        $('#countChart').hide();
        $('#timeChart').show();
      }
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_count') {
        $('#pieChart').hide();
        $('#countChart').show();
        $('#timeChart').hide();
      }
    } 
    else {
      w = global_w;
      h = w/1.7;
      $(containers).each(function(){
        //$(this)[0].setAttribute('viewBox', '0 0 '+ w +' '+ h );
        $(this).attr("width", w).attr("height", h);
      });
      // Adapt main div's padding:
      var div=$('#row_1 .percent_30');
      if (!$(div).hasClass("big_size"))          
          $(div).attr("class",$(div).attr("class")+" big_size");
          
      if ($('a[name=\'cloud_selector\'].active').attr('id') == 'selector_egileak') {
        $('#tagCloud').hide();
        $('#sourceTagCloud').show();
      } 
      else {
        $('#tagCloud').show();
        $('#sourceTagCloud').hide();
      }
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_pie') {
        $('#pieChart').show();
        $('#countChart').hide();
        $('#timeChart').hide();
      }
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_time') {
        $('#pieChart').hide();
        $('#countChart').hide();
        $('#timeChart').show();
      }
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_count') {
        $('#pieChart').hide();
        $('#countChart').show();
        $('#timeChart').hide();
      }
    }
  } 
  else
  img.attr('src', '/static/img/maximize.png');
  return false;
});
$('#tweets .minimize_maximize').click(function () {
  $('#row_2').slideToggle(500);
  var img = $(this).find('img');
  var containers = $(".svg-container svg");

  
  if ($(img).attr('src') == '/static/img/maximize.png') {
    w = $('#tagCloud').parent().parent().width();
    h = $('#tagCloud').parent().parent().width()/3.8;
    $(containers).each(function(){
        //$(this)[0].setAttribute('viewBox', '0 0 '+ w +' '+ h );
        $(this).attr("width", w).attr("height", h);
    });
    img.attr('src', '/static/img/minimize.png');
    if ($('#row_1').css('display') != 'none') {
      if ($('a[name=\'cloud_selector\'].active').attr('id') == 'selector_egileak') { // egileak erakutsi behar dira
        $('#tagCloud').hide();
        $('#sourceTagCloud').show();
      } 
      else {
        $('#tagCloud').show();
        $('#sourceTagCloud').hide();
      }
      var div=$('#row_1 .percent_30');
      if ($(div).hasClass("big_size"))
          $(div).attr("class",$(div).attr("class").replace("big_size",""));
          
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_pie') {
        $('#pieChart').show();
        $('#countChart').hide();
        $('#timeChart').hide();
      }
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_time') {
        $('#pieChart').hide();
        $('#countChart').hide();
        $('#timeChart').show();
      }
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_count') {
        $('#pieChart').hide();
        $('#countChart').show();
        $('#timeChart').hide();
      }
    }
  } 
  else {
    img.attr('src', '/static/img/maximize.png');
    w = $('#tagCloud').parent().parent().width();
    h = $('#tagCloud').parent().parent().width()/1.7;
    $(containers).each(function(){
        //$(this)[0].setAttribute('viewBox', '0 0 '+ w +' '+ h );
        $(this).attr("width", w).attr("height", h);
    });
    if ($('a[name=\'cloud_selector\'].active').attr('id') == 'selector_egileak') {
      
      $('#tagCloud').hide();
      $('#sourceTagCloud').show();
    } 
    else {
      $('#tagCloud').show();
      $('#sourceTagCloud').hide();
    }
    var div=$('#row_1 .percent_30');
    if (!$(div).hasClass("big_size"))          
       $(div).attr("class",$(div).attr("class")+" big_size");
    if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_pie') {
      $('#pieChart').show();
      $('#countChart').hide();
      $('#timeChart').hide();
    }
    if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_time') {
      $('#pieChart').hide();
      $('#countChart').hide();
      $('#timeChart').show();
    }
    if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_count') {
      $('#pieChart').hide();
      $('#countChart').show();
      $('#timeChart').hide();
    }
  }
  return false;
});
$('#orokorra1').parent().click(function () {
  $('.jarri').parent().attr('class', 'btn btn-lg btn-success active');
  $('.kendu').parent().attr('class', 'btn btn-lg btn-danger');
});
$('#orokorra2').parent().click(function () {
  $('.jarri').parent().attr('class', 'btn btn-lg btn-success');
  $('.kendu').parent().attr('class', 'btn btn-lg btn-danger active');
});
//$("#row_2").toggle();
$('input[name=\'options\']').parent().click(function () {
  /*if ($(this).attr("class").indexOf("btn-success") >= 0){
        $("#denak1").parent().attr("class","btn btn-lg btn-success active");
        $("#denak2").parent().attr("class","btn btn-lg btn-danger");
    }*/
  $('input[name=\'options\']').each(function () {
    var parent = $(this).parent();
    if ($(parent).hasClass('btn-danger'))
    $(parent).attr('class', 'btn btn-lg btn-danger');
     else
    $(parent).attr('class', 'btn btn-lg btn-success active');
  })
  //refresh_from_buttons($(this));
  var id = $(this).find('input:first').attr('id');
  if (id.indexOf('1') == - 1) {
    // Botoia sakatu da
    $('#id_category').val(id.replace('2', ''));
    //reload_from_button(id.replace("2",""))        
    id = id.replace('2', '');
  } 
  else {
    $('#id_category').val('');
  }
  $('#id_source').val('');
  $('#id_tag').val('');
  reload_with_filters();
});
$('input[name=\'table_options\']').parent().click(function () {
  $('input[name=\'table_options\']').each(function () {
    var parent = $(this).parent();
    if ($(parent).hasClass('btn-danger'))
    $(parent).attr('class', 'btn btn-lg btn-danger');
     else
    $(parent).attr('class', 'btn btn-lg btn-success active');
  });
  refresh_from_manage_mentions_buttons($(this));
});
//Auto Refresh
var intervalID;
$('input[name=\'options0\']').parent().click(function () {
  if ($(this).find('input').attr('id') == 'option01') {
    intervalID = clearInterval(intervalID);
    intervalID = '';
  } 
  else {
    intervalID = setInterval(function () {
      reload_with_filters();
    }, 900000);
  }
});
var word_cloud;
if (time_neutroak_list == 'undefined')
var time_neutroak_list = [
];
if (time_positiboak_list == 'undefined')
var time_positiboak_list = [
];
if (time_negatiboak_list == 'undefined')
var time_negatiboak_list = [
];
function show_chart(id, width, height) {
  var vis = d3.select('#' + id + ' .visualisation'),
  WIDTH = width,
  HEIGHT = height,
  MARGINS = {
    top: 10,
    right: 40,
    bottom: 10,
    left: 50
  },
  xScale = d3.time.scale().domain([new Date(Date.parse(time_neutroak_list[0].date)),
  d3.time.day.offset(new Date(Date.parse(time_neutroak_list[time_neutroak_list.length - 1].date)), 1)]).rangeRound([50,
  WIDTH - MARGINS.left - MARGINS.right]),
  yScale = d3.scale.linear().domain([0,
  time_neutroak_list_max]).range([HEIGHT - MARGINS.top - MARGINS.bottom,
  6]);
  xAxis = d3.svg.axis().scale(xScale).orient('bottom').tickFormat(d3.time.format('%m-%d')).tickSize(0).ticks(d3.time.days, 5).tickPadding(8);
  yAxis = d3.svg.axis().scale(yScale).orient('left');
  // NEUTROAK
  var lineGen = d3.svg.line().x(function (d) {
    return xScale(new Date(Date.parse(d.date)));
  }).y(function (d) {
    return yScale(d.count);
  });
  //.interpolate("basis");
  vis.append('svg:path').attr('d', lineGen(time_neutroak_list)).attr('stroke', 'grey').attr('stroke-width', 1).attr('fill', 'none');
  vis.append('svg:g').attr('class', 'axis').attr('transform', 'translate(' + (MARGINS.left) + ',0)').call(yAxis);
  vis.append('svg:g').attr('class', 'x axis xasis').attr('transform', 'translate(0, ' + (HEIGHT - MARGINS.top - MARGINS.bottom) + ')').call(xAxis);
  vis.selectAll('.xaxis text') // select all the text elements for the xaxis
  .attr('transform', function (d) {
    return 'translate(' + this.getBBox().height * - 2 + ',' + this.getBBox().height + ')rotate(-45)';
  });
  // POSITIBOAK
  var lineGen = d3.svg.line().x(function (d) {
    return xScale(new Date(Date.parse(d.date)));
  }).y(function (d) {
    return yScale(d.count);
  });
  //.interpolate("basis");
  vis.append('svg:path').attr('d', lineGen(time_positiboak_list)).attr('stroke', 'green').attr('stroke-width', 1).attr('fill', 'none');
  // NEGATIBOAK
  var lineGen = d3.svg.line().x(function (d) {
    return xScale(new Date(Date.parse(d.date)));
  }).y(function (d) {
    return yScale(d.count);
  });
  //.interpolate("basis");
  vis.append('svg:path').attr('d', lineGen(time_negatiboak_list)).attr('stroke', 'red').attr('stroke-width', 1).attr('fill', 'none');
}


function show_pie(id, width, height) {
  var canvasWidth = width;
  var canvasHeight = height;
  var pie = new d3pie(document.getElementById(id), {
    'size': {
      'canvasWidth': canvasWidth,
      'canvasHeight': canvasHeight,
      'pieOuterRadius': '90%'
    },
    'data': {
      'sortOrder': 'value-desc',
      'content': [
        {
          'label': 'Neutroak',
          'value': neutroak,
          'color': '#bfbfbf'
        },
        {
          'label': 'Positiboak',
          'value': positiboak,
          'color': '#56b510'
        },
        {
          'label': 'Negatiboak',
          'value': negatiboak,
          'color': '#ff4141'
        }
      ]
    },
    'labels': {
      'outer': {
        'pieDistance': 12
      },
      'inner': {
        'hideWhenLessThanPercentage': 3
      },
      'mainLabel': {
        'fontSize': 15
      },
      'percentage': {
        'color': '#ffffff',
        'decimalPlaces': 0
      },
      'value': {
        'color': '#adadad',
        'fontSize': 20
      },
      'lines': {
        'enabled': true
      },
      'truncation': {
        'enabled': true
      }
    },
    'effects': {
      'pullOutSegmentOnClick': {
        'effect': 'linear',
        'speed': 400,
        'size': 8
      }
    },
    'misc': {
      'gradient': {
        'enabled': true,
        'percentage': 100
      }
    }
  });
}
function show_tag_cloud(id, width, height) {
  var wordInfo = JSON.parse(lainoa);
  //var wordInfo = JSON.parse('{"eljukebox":"11","dk_casares":"11","Donostiando":"12","BakeaPaz2016":"11","TrendsBeth":"10","keler":"10","suartezLC":"10","DSS2016":"25","cineffo":"11","2016_desokupatu":"11","Elhuyar":"11","Atekarri":"10","DonoSStiaoculta":"11","kabe_jrr":"11","sansebastianfes":"10","patxangas":"11","PetraZabalgana":"10","Emusik2016":"11","elcafederick":"11","sweetlittlehifi":"10","Andres_DiTella":"11","FomentoSS":"11","EgiaSegurua":"10","Imanol_Otaegi":"11","Ricardo_AMASTE":"11","imanolgallego":"10","cristina_enea":"11","donostiakultura":"14","ARQUIMANA":"10","AmagoiaLauzirik":"10","cineccdonostia":"11","kulturklik":"11","SSTurismo":"10","ereitenkz":"10","OlatuTalka":"14","donostia13":"10","egarate":"10","Feministaldia":"10","kutxakultur":"11","Donostilandia":"10","DavidJcome1":"12","AizpeaOM":"10","AATOMIC_LAB":"10","Elsekadero":"11","Zinea_eus":"11","MenofRockMusika":"10","foteropanico":"11","kutxakulturfest":"10","aquariumss":"10","paolaguimerans":"11","hirikilabs":"12","anderm68":"11","DSS2016Europe":"12","anestraat":"11","kortxoenea":"11","EUDialogues":"11","iortizgascon":"11","Carlos_Elorza":"11","Dricius":"11","filmotecavasca":"11","irutxulo":"11","fabusca":"12","jonpagola":"10","MirenMartin":"10","Poulidor77":"10","diariovasco":"10","joxeanurkiola":"10","xabipaya":"12","AsierBA85":"11","digilizar":"10","tabakalera":"17","MusicBox2016":"11","kulturaldia":"11","danilo_starz_":"10","interzonasinfo":"10","LaGuipuzcoana":"10","ARTEKLAB":"11","im_probables":"11","EnekoOlasagasti":"10","DJacomeNorato":"11","sonidoalpha":"12","Bihurgunea":"12","Bitorikova":"10","enekogoia":"11","AEGIkastetxea":"11","Amarapedia":"10","enarri":"10","garbibai":"10","djjacomenorato":"13","anerodriguez_a":"10","maiurbel":"10","raldarondo":"11","LaPublika":"10","GipuzkoadeModa":"11","DK_Liburutegiak":"11","Perutzio":"10","musiceoso":"10","e2020dss":"10","koldoartola":"10","ColaBoraBora":"11"}');
  var fill = d3.scale.category20();
  //var fontSize = d3.scale.log().range([10, 100]);
  //var width = $('#tagCloud').parent().parent().width();
  var textScale=d3.scale.log().range([1, 14]);
  var w = width;
  var h = height;
  word_cloud = d3.layout.cloud().size([w,
  h]).words(Object.keys(wordInfo).map(function (d) {
    return {
      text: d,
      size: wordInfo[d]
    };
  })).padding(1).timeInterval(400).rotate(function () {
    return ~~(Math.random() * 2) * 0;
  }).font('Impact').fontSize(function(d){
	    var window_width=$(window).width();
            if (window_width<800)
                return textScale(d.size/2.5);
            else            
                return textScale(d.size);
	}).on('end', draw).start();
  function draw(words) {
    /*d3.select(id).append('svg').attr('width', w).attr('height', h).append('g').attr('transform', 'translate(' + [w >> 1,
    h >> 1] + ')').selectAll('text').data(words).enter().append('text')
    //.style("font-size", function(d) { return d.size + "px"; })
    .style('font-size', function (d) {
      return d.size + 'px';
    })
    //.style("font-size", function(d) { return Math.min( d.size,  d.size/this.getComputedTextLength() * 24) + "px"; })
    .style('font-family', 'Impact').style('text-color', 'black').style('fill', function (d, i) {
      return fill(i);
    }).attr('text-anchor', 'middle').attr('transform', function (d) {
      return 'translate(' + [d.x,
      d.y] + ')rotate(' + d.rotate + ')';
    }).text(function (d) {
      return d.text;
    }).on('click', function (d) {
      reload_from_tag(d.text);
    }
    ).on('mouseover', function (d) {
      document.body.style.cursor = 'pointer';
    }
    ).on('mouseout', function (d) {
      document.body.style.cursor = 'default';
    }
    );*/
    var svg = d3.select(id)
		.append("div")
		.classed("svg-container", true) //container class to make it responsive
		.append("svg")
                 //responsive SVG needs these 2 attributes and no width and height attr
		.attr("preserveAspectRatio", "none") //"xMinYMin meet")
		.attr("viewBox",  0 + " " + 0 + " " + w + " " + h)
	    //class to make it responsive
		.classed("svg-content-responsive", true); 
		//.attr("width", w) 
                //.attr("height", h)

              svg.append("g")
                .attr("transform", "translate("+ [w >> 1, h >> 1] +")")
              .selectAll("text")
                .data(words)       
		.enter().append("text")
                //.style("font-size", function(d) { return d.size + "px"; })
	        .style("font-size", function(d) { return d.size + "px"; })
                //.style("font-size", function(d) { return Math.min( d.size,  d.size/this.getComputedTextLength() * 24) + "px"; })
		.style("font-family", "Impact")
	        .style("text-color", "black")
                .style("fill", function(d, i) { return fill(i); })
                .attr("text-anchor", "middle")
                .attr("transform", function(d) {
                    return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
                })
                .text(function(d) { return d.text; })
                .on("click", function(d) {
                        reload_from_tag(d.text); }
                 ).on("mouseover", function(d) {
                        document.body.style.cursor = 'pointer'; }
                 )
                 .on("mouseout", function(d) {
                        document.body.style.cursor = 'default'; }
                 );
    if ('author' == 'author')
    {
      //document.getElementById('tagCloud').style.display="none";
    }
  }
  /*
        function draw(words) {
              d3.select(id).append("svg")
                .attr("width", w) 
                .attr("height", h)
              .append("g")
                .attr("transform", "translate("+ [w >> 1, h >> 1] +")")
              .selectAll("text")
                .data(words)       
		.enter().append("text")
	        .attr("text-anchor", "middle")	        
		.each(function(d){
		    d3.select(this).append("tspan")
			.style("font-size", function(r) { return d.size + "px"; })
			.style("font-family", "Impact")
			.style("fill", "black")  //function(d, i) { return fill(i); })
			.attr("text-anchor", "middle")
			.attr("dy",0)
			.attr("x",0)
			.text(function(r) { return r.text; });
		    d3.select(this).append("tspan")
			.style("font-size", function(r) { return (d.size-5) + "px"; })
			.style("font-family", "Impact")
			.style("fill", "green") //.style("fill", function(d, i) { return fill(i); })
			.attr("text-anchor", "middle")
			.attr("dy",function(r){return (d.size*0.6) + "px";})
			.attr("x",0)
			.text(function(r) { return r.text; });
		    d3.select(this).append("tspan")
			.style("font-size", function(r) { return (d.size-5) + "px"; })
			.style("font-family", "Impact")
			.style("fill", "red")  //.style("fill", function(d, i) { return fill(i); })
			.attr("text-anchor", "middle")
			.attr("dy",function(r){return (d.size) + "px";})
			.attr("x",0)
			.text(function(r) { return r.text; });
		})
		.attr("transform", function(d) {
		    return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";});

            if ("author" == "author")
            {
	        //document.getElementById('tagCloud').style.display="none";
            }
        }
*/

}
function show_source_tag_cloud(id, width, height) {
  var wordInfo = JSON.parse(source_lainoa);
  //var wordInfo = JSON.parse('{"eljukebox":"11","dk_casares":"11","Donostiando":"12","BakeaPaz2016":"11","TrendsBeth":"10","keler":"10","suartezLC":"10","DSS2016":"25","cineffo":"11","2016_desokupatu":"11","Elhuyar":"11","Atekarri":"10","DonoSStiaoculta":"11","kabe_jrr":"11","sansebastianfes":"10","patxangas":"11","PetraZabalgana":"10","Emusik2016":"11","elcafederick":"11","sweetlittlehifi":"10","Andres_DiTella":"11","FomentoSS":"11","EgiaSegurua":"10","Imanol_Otaegi":"11","Ricardo_AMASTE":"11","imanolgallego":"10","cristina_enea":"11","donostiakultura":"14","ARQUIMANA":"10","AmagoiaLauzirik":"10","cineccdonostia":"11","kulturklik":"11","SSTurismo":"10","ereitenkz":"10","OlatuTalka":"14","donostia13":"10","egarate":"10","Feministaldia":"10","kutxakultur":"11","Donostilandia":"10","DavidJcome1":"12","AizpeaOM":"10","AATOMIC_LAB":"10","Elsekadero":"11","Zinea_eus":"11","MenofRockMusika":"10","foteropanico":"11","kutxakulturfest":"10","aquariumss":"10","paolaguimerans":"11","hirikilabs":"12","anderm68":"11","DSS2016Europe":"12","anestraat":"11","kortxoenea":"11","EUDialogues":"11","iortizgascon":"11","Carlos_Elorza":"11","Dricius":"11","filmotecavasca":"11","irutxulo":"11","fabusca":"12","jonpagola":"10","MirenMartin":"10","Poulidor77":"10","diariovasco":"10","joxeanurkiola":"10","xabipaya":"12","AsierBA85":"11","digilizar":"10","tabakalera":"17","MusicBox2016":"11","kulturaldia":"11","danilo_starz_":"10","interzonasinfo":"10","LaGuipuzcoana":"10","ARTEKLAB":"11","im_probables":"11","EnekoOlasagasti":"10","DJacomeNorato":"11","sonidoalpha":"12","Bihurgunea":"12","Bitorikova":"10","enekogoia":"11","AEGIkastetxea":"11","Amarapedia":"10","enarri":"10","garbibai":"10","djjacomenorato":"13","anerodriguez_a":"10","maiurbel":"10","raldarondo":"11","LaPublika":"10","GipuzkoadeModa":"11","DK_Liburutegiak":"11","Perutzio":"10","musiceoso":"10","e2020dss":"10","koldoartola":"10","ColaBoraBora":"11"}');
  var fill = d3.scale.category20();
  //var fontSize = d3.scale.log().range([10, 100]);
  //var width = $('#tagCloud').parent().parent().width();
  var w = width;
  var h = height;
  word_cloud = d3.layout.cloud().size([w,
  h]).words(Object.keys(wordInfo).map(function (d) {
    return {
      text: d,
      size: wordInfo[d]
    };
  })).padding(1).timeInterval(400).rotate(function () {
    return ~~(Math.random() * 2) * 0;
  }).font('Impact').fontSize(function (d) {
    var window_width = $(window).width();
    if (window_width < 800)
    return d.size / 2.5;
     else
    return d.size;
  }).on('end', draw).start();
  function draw(words) {
    var svg = d3.select(id)
		.append("div")
		.classed("svg-container", true) //container class to make it responsive
		.append("svg")
                 //responsive SVG needs these 2 attributes and no width and height attr
		.attr("preserveAspectRatio", "none") //"xMinYMin meet")
		.attr("viewBox",  0 + " " + 0 + " " + w + " " + h)
	    //class to make it responsive
		.classed("svg-content-responsive", true); 
		//.attr("width", w) 
                //.attr("height", h)

              svg.append("g")
                .attr("transform", "translate("+ [w >> 1, h >> 1] +")")
              .selectAll("text")
                .data(words)       
		.enter().append("text")
                //.style("font-size", function(d) { return d.size + "px"; })
	        .style("font-size", function(d) { return d.size + "px"; })
                //.style("font-size", function(d) { return Math.min( d.size,  d.size/this.getComputedTextLength() * 24) + "px"; })
		.style("font-family", "Impact")
	        .style("text-color", "black")
                .style("fill", function(d, i) { return fill(i); })
                .attr("text-anchor", "middle")
                .attr("transform", function(d) {
                    return "translate(" + [d.x, d.y] + ")rotate(" + d.rotate + ")";
                })
                .text(function(d) { return d.text; })
                .on("click", function(d) {
                        reload_from_user(d.text); }
                 ).on("mouseover", function(d) {
                        document.body.style.cursor = 'pointer'; }
                 )
                 .on("mouseout", function(d) {
                        document.body.style.cursor = 'default'; }
                 );
    if ('author' == 'author')
    {
      //document.getElementById('tagCloud').style.display="none";
    }
  }
}


function show_bar_chart(id,categories,values){


		var colors = ['#0000b4','#0082ca','#0094ff','#0d4bcf','#0066AE','#074285','#00187B','#285964','#405F83','#416545','#4D7069','#6E9985','#7EBC89','#0283AF','#79BCBF','#99C19E','#0000b4','#0082ca','#0094ff','#0d4bcf','#0066AE'];

		var grid = d3.range(25).map(function(i){
			return {'x1':0,'y1':0,'x2':0,'y2':480};
		});

		var tickVals = grid.map(function(d,i){
			if(i>0){ return i*100000; }
			else if(i===0){ return "100000";}
		});

		var xscale = d3.scale.linear()
						.domain([0,Math.max.apply(Math,values)])
						.range([0,150]);

		var yscale = d3.scale.linear()
						.domain([0,categories.length])
						.range([0,450]);

		var colorScale = d3.scale.quantize()
						.domain([0,categories.length])
						.range(colors);

		var canvas = d3.select('#'+id)
						.append('svg')
						.attr({'width':'350','height':550});

		var grids = canvas.append('g')
						  .attr('id','grid')
						  .attr('transform','translate(150,10)')
						  .selectAll('line')
						  .data(grid)
						  .enter()
						  .append('line')
						  .attr({'x1':function(d,i){ return i*30; },
								 'y1':function(d){ return d.y1; },
								 'x2':function(d,i){ return i*30; },
								 'y2':function(d){ return d.y2; },
							})
						  .style({'stroke':'#adadad','stroke-width':'1px'});

		var	xAxis = d3.svg.axis();
			xAxis
				.orient('bottom')
				.scale(xscale)
				.tickValues(tickVals);

		var	yAxis = d3.svg.axis();
			yAxis
				.orient('left')
				.scale(yscale)
				.tickSize(2)
				.tickFormat(function(d,i){ return categories[i]; })
				.tickValues(d3.range(20));

		var y_xis = canvas.append('g')
						  .attr("transform", "translate(150,30)")
						  .attr('id','yaxis')
						  .attr('style',"font-size:12px")
						  .call(yAxis);

		var x_xis = canvas.append('g')
						  .attr("transform", "translate(150,480)")
						  .attr('id','xaxis')
						  .call(xAxis);

		var chart = canvas.append('g')
							.attr("transform", "translate(150,0)")
							.attr('id','bars')
							.selectAll('rect')
							.data(values)
							.enter()
							.append('rect')
							.attr('height',19)
							.attr({'x':0,'y':function(d,i){ return yscale(i)+21; }})
							.style('fill',function(d,i){ return colorScale(i); })
							.attr('width',function(d){ return xscale(d); });


		var transit = d3.select("svg").selectAll("rect")
						    .data(values)
						    .transition()
						    .duration(1000) 
						    .attr("width", function(d) {return xscale(d)/5; });

		var transitext = d3.select('#'+id+' #bars')
							.selectAll('text')
							.data(values)
							.enter()
							.append('text')
							.attr({'x':function(d) {return xscale(d); },'y':function(d,i){ return yscale(i)+35; }})
							.text(function(d){ return d; }).style({'fill':'black','font-size':'12px'});


                



}

/* Hasieratu grafikoak */

var global_w;

function main_page_graphs() {
  global_w = $('#tagCloud').parent().parent().width();
  show_tag_cloud('#tagCloud', $('#tagCloud').parent().parent().width(), $('#tagCloud').parent().parent().width() / 3.8);
  show_source_tag_cloud('#sourceTagCloud', $('#tagCloud').parent().parent().width(), $('#tagCloud').parent().parent().width() / 3.8);
  show_pie('pieChart', $('#pieChart').width(), $('#pieChart').width() / 2.1);
  show_chart('timeChart', $('#timeChart').width() * 1.1, $('#timeChart').width() /2);
  //$('#tagCloud').toggle();
  $('#timeChart').toggle();
  $('#countChart').toggle();
  $('#sourceTagCloud').toggle();
}
function stats_page_graphs() {
  //show_pie('pieChart', $('#pieChart').width() * 0.6, $('#pieChart').width() * 0.4);
  show_chart('timeChart', $('#timeChart').width()*1.2, $('#timeChart').width()*0.2);
  show_bar_chart('barChartAll',top_keyword_categories,top_keyword_values);
  show_bar_chart('barChartPos',top_keyword_categories_pos,top_keyword_values_pos);
  show_bar_chart('barChartNeg',top_keyword_categories_neg,top_keyword_values_neg);
  show_bar_chart('barChart2All',top_media_categories,top_media_values);
  show_bar_chart('barChart2Pos',top_media_categories_pos,top_media_values_pos);
  show_bar_chart('barChart2Neg',top_media_categories_neg,top_media_values_neg);
  show_bar_chart('barChart3All',top_twitter_categories,top_twitter_values);
  show_bar_chart('barChart3Pos',top_twitter_categories_pos,top_twitter_values_pos);
  show_bar_chart('barChart3Neg',top_twitter_categories_neg,top_twitter_values_neg);
}

function stats_page_filters(){
  
  $("#id_category").change(function(){
  $.ajax({
    method: 'GET',
    url: '/behagunea/reload_projects_filter',
    dataType: 'html',
    data: {
      category: $(this).val()
    }
  }).done(function (data) {
    $("#id_project").html(data)
  });
  
  });
}

$('a[name=\'graph_selector\']').click(function () {
  if ($(this).attr('id') == 'selector_pie') {
    $('#selector_pie').attr('class', 'active');
    $('#selector_pie img').attr('src', '/static/img/pie_selected.png');
    $('#selector_time').attr('class', '');
    $('#selector_time img').attr('src', '/static/img/chart.png');
    $('#selector_count').attr('class', '');
    $('#selector_count img').attr('src', '/static/img/count.png');
    var img = $('#tweets h3 img');
    if ($(img).attr('src') == '/static/img/maximize.png') {
      if ($('#row_1').css('display') != 'none') {
        $('#pieChart').show();
        $('#timeChart').hide();
        $('#countChart').hide();
      }
    } 
    else {
      $('#pieChart').show();
      $('#timeChart').hide();
      $('#countChart').hide();
    }
  }
  if ($(this).attr('id') == 'selector_time') {
    $('#selector_pie').attr('class', '');
    $('#selector_pie img').attr('src', '/static/img/pie.png');
    $('#selector_time').attr('class', 'active')
    $('#selector_time img').attr('src', '/static/img/chart_selected.png');
    $('#selector_count').attr('class', '');
    $('#selector_count img').attr('src', '/static/img/count.png');
    var img = $('#tweets h3 img');
    if ($(img).attr('src') == '/static/img/maximize.png') {
      if ($('#row_1').css('display') != 'none') {
        $('#pieChart').hide();
        $('#timeChart').show();
        $('#countChart').hide();
      }
    } 
    else {
      $('#pieChart').hide();
      $('#timeChart').show();
      $('#countChart').hide();
    }
  }
  if ($(this).attr('id') == 'selector_count') {
    $('#selector_pie').attr('class', '');
    $('#selector_pie img').attr('src', '/static/img/pie.png');
    $('#selector_time').attr('class', '')
    $('#selector_time img').attr('src', '/static/img/chart.png');
    $('#selector_count').attr('class', 'active');
    $('#selector_count img').attr('src', '/static/img/count_selected.png');
    var img = $('#tweets h3 img');
    if ($(img).attr('src') == '/static/img/maximize.png') {
      if ($('#row_1').css('display') != 'none') {
        $('#pieChart').hide();
        $('#timeChart').hide();
        $('#countChart').show();
      }
    } 
    else {
      $('#pieChart').hide();
      $('#timeChart').hide();
      $('#countChart').show();
    }
  }
});
$('a[name=\'cloud_selector\']').click(function () {
  if ($(this).attr('id') == 'selector_egileak') {
    $('#selector_egileak').attr('class', 'active');
    $('#selector_gakoak').attr('class', '')
    var img = $('#tweets h3 img');
    if ($(img).attr('src') == '/static/img/maximize.png') {
      if ($('#row_1').css('display') != 'none') {
        $('#sourceTagCloud').show();
        $('#tagCloud').hide();
        //$('#pieChart').show();  
        if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_pie') {
          $('#pieChart').show();
          $('#countChart').hide();
          $('#timeChart').hide();
        }
        if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_time') {
          $('#pieChart').hide();
          $('#countChart').hide();
          $('#timeChart').show();
        }
        if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_count') {
          $('#pieChart').hide();
          $('#countChart').show();
          $('#timeChart').hide();
        }
      }
    } 
    else {

      $('#sourceTagCloud').show();
      $('#tagCloud').hide();
      //$('#pieChart').hide();
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_pie') {
        $('#pieChart').show();
        $('#countChart').hide();
        $('#timeChart').hide();
      }
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_time') {
        $('#pieChart').hide();
        $('#countChart').hide();
        $('#timeChart').show();
      }
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_count') {
        $('#pieChart').hide();
        $('#countChart').show();
        $('#timeChart').hide();
      }
    }
  } 
  else {
    $('#selector_egileak').attr('class', '');
    $('#selector_gakoak').attr('class', 'active')
    var img = $('#tweets h3 img');
    if ($(img).attr('src') == '/static/img/maximize.png') {
      if ($('#row_1').css('display') != 'none') {
        $('#sourceTagCloud').hide();
        $('#tagCloud').show();
        //$('#pieChart').show();     
        if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_pie') {
          $('#pieChart').show();
          $('#countChart').hide();
          $('#timeChart').hide();
        }
        if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_time') {
          $('#pieChart').hide();
          $('#countChart').hide();
          $('#timeChart').show();
        }
        if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_count') {
          $('#pieChart').hide();
          $('#countChart').show();
          $('#timeChart').hide();
        }
      }
    } 
    else {
      
      $('#sourceTagCloud').hide();
      $('#tagCloud').show();
      //$('#pieChart').hide();
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_pie') {
        $('#pieChart').show();
        $('#countChart').hide();
        $('#timeChart').hide();
      }
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_time') {
        $('#pieChart').hide();
        $('#countChart').hide();
        $('#timeChart').show();
      }
      if ($('a.active[name=\'graph_selector\']').attr('id') == 'selector_count') {
        $('#pieChart').hide();
        $('#countChart').show();
        $('#timeChart').hide();
      }
    }
  }
});



function reload_from_user(username) {
  $('#id_source').val(username);
  $('#id_tag').val('');
  reload_with_filters();
}
function reload_from_tag(tag) {
  $('#id_tag').val(tag);
  $('#id_source').val('');
  reload_with_filters();
}
function refresh_from_manage_mentions_buttons(button) {
  var id = $(button).find('input:first').attr('id');
  if (id.indexOf('1') == - 1) {
    // Botoia sakatu da
    reload_from_manage_mentions_button(id.replace('2', ''))
  } 
  else {
    //reload_all();
  }
}
/* HAU DA ONA!*/

function reload_with_filters() {
  //category = get_active_button();
  $('#loading_modal').modal('show');
  //$("#id_category").val(category);
  $.ajax({
    method: 'GET',
    url: '/behagunea/reload_page',
    dataType: 'html',
    data: {
      category: $('#id_category').val(),
      tag: $('#id_tag').val(),
      user: $('#id_user').val(),
      date: $('#id_date').val(),
      lang: $('#id_lang').val(),
      influence: $('#id_influence').val(),
      source: $('#id_source').val(),
      type: $('#id_type').val()
    }
  }).done(function (data) {
    var new_row = $(data) [0];
    neutroak = parseInt($(data) [2].innerHTML);
    positiboak = parseInt($(data) [4].innerHTML);
    negatiboak = parseInt($(data) [6].innerHTML);
    lainoa = $(data) [8].innerHTML;
    source_lainoa = $(data) [10].innerHTML;
    information_tag = $(data) [12].innerHTML;
    if ($('#id_source').val() == '' && $('#id_tag').val() == '') {
      w = $('#tagCloud').parent().parent().width();
      h = $('#tagCloud').parent().parent().height();
      $('#tagCloud div').remove();
      $('#sourceTagCloud div').remove();
      
      show_tag_cloud('#tagCloud', w, h);      
      show_source_tag_cloud('#sourceTagCloud', w, h);
      
    }
    $('#row_2').html(new_row);
    $('#pieChart svg').remove();
    show_pie('pieChart', $('#pieChart').width(), $('#pieChart').width() / 1.7);
    $('.aipamen_kopurua').html($(data) [20].innerHTML);
    $('.positibo_kopurua').html($(data) [16].innerHTML);
    $('.negatibo_kopurua').html($(data) [18].innerHTML);
    $('.neutro_kopurua').html($(data) [14].innerHTML);
    time_neutroak_list = $.makeArray($(data) [22].innerHTML.split('|'));
    if (time_neutroak_list[0] != '')
    time_neutroak_list = $.map(time_neutroak_list, function (n) {
      return $.parseJSON(n.replace(/\'/g, '"'));
    });
    time_neutroak_list_max = $(data) [24].innerHTML;
    time_positiboak_list = $.makeArray($(data) [26].innerHTML.split('|'));
    if (time_positiboak_list[0] != '')
    time_positiboak_list = $.map(time_positiboak_list, function (n) {
      return $.parseJSON(n.replace(/\'/g, '"'));
    });
    time_positiboak_list_max = $(data) [28].innerHTML;
    time_negatiboak_list = $.makeArray($(data) [30].innerHTML.split('|'));
    if (time_negatiboak_list[0] != '')
    time_negatiboak_list = $.map(time_negatiboak_list, function (n) {
      return $.parseJSON(n.replace(/\'/g, '"'));
    });
    time_negatiboak_list_max = $(data) [32].innerHTML;
    $('#timeChart svg').remove();
    $('#timeChart').html('<svg class="visualisation" style="width: 90%;height: 200px;"></svg>');
    show_chart('timeChart', $('#timeChart').width() * 1.2, $('#timeChart').width() /2);
    $('#tweets div h3 span').text('(' + information_tag + ')');
    
    eval($(data) [34].innerHTML);
    
    $('#loading_modal').modal('hide');
  });
}

function reload_with_filters_stats() {
  $('#loading_modal').modal('show');
  $.ajax({
    method: 'GET',
    url: '/behagunea/reload_page_stats/',
    dataType: 'html',
    data: {
      date_b: $('#id_date_b').val(),
      date_e: $('#id_date_e').val(),
      category: $('#id_category').val(),
      project: $('#id_project').val()
    }
  }).done(function (data) {
    time_neutroak_list = $.makeArray($(data) [0].innerHTML.split('|'));
    if (time_neutroak_list[0] != '')
    time_neutroak_list = $.map(time_neutroak_list, function (n) {
      return $.parseJSON(n.replace(/\'/g, '"'));
    });
    time_neutroak_list_max = $(data) [2].innerHTML;
    time_positiboak_list = $.makeArray($(data) [4].innerHTML.split('|'));
    if (time_positiboak_list[0] != '')
    time_positiboak_list = $.map(time_positiboak_list, function (n) {
      return $.parseJSON(n.replace(/\'/g, '"'));
    });
    time_positiboak_list_max = $(data) [6].innerHTML;
    time_negatiboak_list = $.makeArray($(data) [8].innerHTML.split('|'));
    if (time_negatiboak_list[0] != '')
    time_negatiboak_list = $.map(time_negatiboak_list, function (n) {
      return $.parseJSON(n.replace(/\'/g, '"'));
    });
    time_negatiboak_list_max = $(data) [10].innerHTML;
    top_keyword_categories = JSON.parse($(data) [12].innerHTML);
    top_keyword_values = JSON.parse($(data) [14].innerHTML);
    top_keyword_categories_pos = JSON.parse($(data) [16].innerHTML);
    top_keyword_values_pos = JSON.parse($(data) [18].innerHTML);
    top_keyword_categories_neg = JSON.parse($(data) [20].innerHTML);
    top_keyword_values_neg = JSON.parse($(data) [22].innerHTML);
    top_media_categories = JSON.parse($(data) [24].innerHTML);
    top_media_values = JSON.parse($(data) [26].innerHTML);
    top_media_categories_pos = JSON.parse($(data) [28].innerHTML);
    top_media_values_pos = JSON.parse($(data) [30].innerHTML);
    top_media_categories_neg = JSON.parse($(data) [32].innerHTML);
    top_media_values_neg = JSON.parse($(data) [34].innerHTML);
    top_twitter_categories = JSON.parse($(data) [36].innerHTML);
    top_twitter_values = JSON.parse($(data) [38].innerHTML);
    top_twitter_categories_pos = JSON.parse($(data) [40].innerHTML);
    top_twitter_values_pos = JSON.parse($(data) [42].innerHTML);
    top_twitter_categories_neg = JSON.parse($(data) [44].innerHTML);
    top_twitter_values_neg = JSON.parse($(data) [46].innerHTML);
    $('#timeChart svg').remove();
    $('#timeChart').html('<svg class="visualisation" style="width:90%;height:300px;"></svg>');
    $('#barChartAll svg').remove();
    $('#barChartPos svg').remove();
    $('#barChartNeg svg').remove();
    $('#barChart2All svg').remove();
    $('#barChart2Pos svg').remove();
    $('#barChart2Neg svg').remove();
    $('#barChart3All svg').remove();
    $('#barChart3Pos svg').remove();
    $('#barChart3Neg svg').remove();
    show_chart('timeChart', $('#timeChart').width()*1.2, $('#timeChart').width()*0.2);
    show_bar_chart('barChartAll',top_keyword_categories,top_keyword_values);
    show_bar_chart('barChartPos',top_keyword_categories_pos,top_keyword_values_pos);
    show_bar_chart('barChartNeg',top_keyword_categories_neg,top_keyword_values_neg);
    show_bar_chart('barChart2All',top_media_categories,top_media_values);
    show_bar_chart('barChart2Pos',top_media_categories_pos,top_media_values_pos);
    show_bar_chart('barChart2Neg',top_media_categories_neg,top_media_values_neg);
    show_bar_chart('barChart3All',top_twitter_categories,top_twitter_values);
    show_bar_chart('barChart3Pos',top_twitter_categories_pos,top_twitter_values_pos);
    show_bar_chart('barChart3Neg',top_twitter_categories_neg,top_twitter_values_neg);
    $('#loading_modal').modal('hide');
  });
}
function reload_from_manage_mentions_button(category) {
  $('#loading_modal').modal('show');
  $.ajax({
    method: 'GET',
    url: '/behagunea/reload_manage_mentions_page',
    dataType: 'html',
    data: {
      category: category
    }
  }).done(function (data) {
    var new_row = $(data) [0];
    $('.container table').parent().html(new_row);
    $('#loading_modal').modal('hide');
  });
}
function reload_all() {
  $('.jarri').parent().attr('class', 'btn btn-lg btn-success active');
  $('.kendu').parent().attr('class', 'btn btn-lg btn-danger');
  $('#id_source').val('');
  $('#id_tag').val('');
  $('#id_category').val('');
  $('#id_date').val('');
  $('#id_influence').val('');
  $('#id_lang').val('');
  $('#id_type').val('');
  reload_with_filters();
  $('#loading_modal').modal('show');
}
$('table input').click(function () {
  if ($(this).prop('checked')) {
    update_polarity($(this));
  } 
  else {
    $(this).prop('checked', true);
  }
});
function table_click(input) {
  if ($(input).prop('checked')) {
    update_polarity($(input));
  } 
  else {
    $(input).prop('checked', true);
  }
}
function update_polarity(check) {
  $.ajax({
    method: 'GET',
    url: '/behagunea/update_polarity',
    dataType: 'html',
    data: {
      polarity: $(check).val(),
      id: $(check).parent().parent().attr('id')
    }
  }).done(function (data) {
    var div = $(check).parent();
    $(div).find('input').prop('checked', false);
    $(check).prop('checked', true);
    $(check).parent().parent().attr('class', 'corrected');
    $(check).parent().parent().attr('name', $(check).val());
  });
}
function load_keyword_form(id) {
  // load from AJAX
  $.ajax({
    method: 'GET',
    url: '/behagunea/keyword_form',
    dataType: 'html',
    data: {
      id: id
    }
  }).done(function (data) {
    $('.keywordmodal-container').parent().html(data);
  });
}
function show_filter() {
  $('#filter_div').slideToggle(500);
  if ($('#filter_button').attr('class') == 'active')
  $('#filter_button').attr('class', '');
   else
  $('#filter_button').attr('class', 'active');
  return false;
}
function delete_mention(id) {
  var response = confirm('Ziur zaude ' + id + ' aipamena ezabatu nahi duzula?');
  if (response) {
    $.ajax({
      method: 'GET',
      url: '/behagunea/delete_mention',
      dataType: 'html',
      data: {
        id: id
      }
    }).done(function (data) {
      //$("#"+id).remove();
      $('#' + id).fadeOut(300, function () {
        $(this).remove();
      });
    });
  }
}

