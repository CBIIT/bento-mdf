$( function () {
  var model = L.map('model', {
    crs: L.CRS.Simple,
    minZoom: -3,
    zoomSnap: 1,
    bounceAtZoomLimits: true,
  });
  let BB = $("#graph").find('svg').children('g').get(0).getBBox();
  let nb = setup_node_select(model,BB.width+BB.x,BB.y)
  var bounds = [[BB.y,BB.width+BB.x],[BB.height+BB.y,BB.x]]
  var image = L.svgOverlay($("#graph").find('svg').get(0), bounds).addTo(model)
  model.fitBounds(bounds)
  // L.polygon(nb.adverse_event.rect,{color: 'lightblue'}).addTo(model)
  start = undefined
  for (i of ['case','Case', 'patient','Patient', 'participant','Participant']) {
    start = $("#node_select").find('option[value='+i+']')
    if (start.get(0)) break;
  }
  if (!start.get(0)) { // default to the first node in list
    start = $("#node_select").find('option').get(1)
    start = $("#node_select").find('option[value='+start.value+']')
  }
  start.attr("selected",true)
  model.flyToBounds(nb[start.get(0).value].bounds)
})
function setup_node_select(model,X,Y) {
  let nb = get_node_bounds(X,Y);
  Object.keys(nb).sort()
    .forEach( function (item) {
      $("#node_select")
	.append($('<option value="'+item+'">'+item+'</option>'))
    })
  $("#node_select")
    .change( function () {
      model.flyToBounds(nb[$("#node_select").get(0).value].bounds)
    })
  return nb
}
function get_node_bounds(X,Y) {
  let ret={}
  $('svg').find('.node')
    .each( function () {
      // let bb =this.getBBox()
      let bb = bbox_from_elt(this)
      ret[$(this).find('title').text().trim()]={ bounds:[ [Y-bb.y, bb.x], [Y-bb.y-bb.height,bb.x+bb.width] ],
					  rect: [ [Y-bb.y,bb.x], [Y-bb.y,bb.x+bb.width],
						  [Y-bb.y-bb.height,bb.x+bb.width],
						  [Y-bb.y-bb.height,bb.x] ] }
    })
  return ret
}

function bbox_from_elt(elt) {
  let a = $(elt).find('path,ellipse')
  let b={}
  if (a.get(0).tagName == "path") {
    let s = attr('d').split(/[MC ]/);
    s.splice(0,4)
    for ( let i=0 ; i<a.length ; i=i+3 ) {
      let w = a[i].split(',').map( x => Number(x) ) ;
      b.xmax = (i==0) ? w[0]: Math.max(b.xmax,w[0]);
      b.xmin = (i==0) ? w[0] : Math.min(b.xmin, w[0]);
      b.ymax = (i==0) ? w[1] : Math.max(b.ymax,w[1]) ;
      b.ymin = (i==0) ? w[1] : Math.min(b.ymin,w[1]) ;
    }
    b.width = b.xmax - b.xmin ; b.height = b.ymax-b.ymin ;
    b.x = b.xmin ; b.y = b.ymin ;
  }
  else if (a.get(0).tagName == "ellipse") {
    b.width = 2.0*a.attr('rx')
    b.height = 2.*a.attr('ry')
    b.xmax = a.attr('cx')+a.attr('rx')
    b.xmin = a.attr('cx')-a.attr('rx')
    b.ymax = a.attr('cy')+a.attr('ry')
    b.ymin = a.attr('cy')-a.attr('ry')
    b.x = b.xmin
    b.y = b.ymin
  }
  return b
}

  

  
