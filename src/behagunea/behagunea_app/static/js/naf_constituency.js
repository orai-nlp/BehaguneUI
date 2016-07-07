var treeData = window.constituencyTree;

// ************** Generate the tree diagram  *****************
var margin = {top: 20, right: 40, bottom: 20, left: 120},
 width = 2500 - margin.right - margin.left,
 height = 2 * 960 - margin.top - margin.bottom;
 
var i = 0;

var tree = d3.layout.tree()
 .size([height, width]);

var diagonal = d3.svg.diagonal()
 .projection(function(d) { return [d.x, d.y]; });

var svg = d3.select("#constituency").append("svg")
 .attr("width", width + margin.right + margin.left)
 .attr("height", height + margin.top + margin.bottom)
 .append("g")
 .attr("transform", "translate(" + margin.top + "," + margin.left + ")");

root = treeData[0];
  
update(root);

$('#constituency').append(
  $('<a>')
    .attr('href-lang', 'image/svg+xml')
    .attr('href', 'data:image/svg+xml;utf8,' +  unescape($('svg')[0].outerHTML))
    .text('Download Tree File')
);

function update(source) {

  // Compute the new tree layout.
  var nodes = tree.nodes(root).reverse(),
   links = tree.links(nodes);

  // Normalize for fixed-depth.
  nodes.forEach(function(d) { d.y = d.depth * 100; });

  // Declare the nodesâ€¦
  var node = svg.selectAll("g.node")
   .data(nodes, function(d) { return d.id || (d.id = ++i); });

  // Enter the nodes.
  var nodeEnter = node.enter().append("g")
   .attr("class", "node")
   .attr("transform", function(d) { 
    return "translate(" + d.x + "," + d.y + ")"; });

  nodeEnter.append("circle")
   .attr("r", 10)
   .style("fill", function(d) { return d.level; });

  nodeEnter.append("text")
   .attr("y", function(d) { 
    return d.children || d._children ? -18 : 18; })
   .attr("dy", ".35em")
   .attr("text-anchor", function(d) { 
    return d.children || d._children ? "end" : "start"; })
   .text(function(d) { return d.name; })
   .style("fill-opacity", 1);

  // Declare the linksâ€¦
  var link = svg.selectAll("path.link")
   .data(links, function(d) { return d.target.id; });

  // Enter the links.
  link.enter().insert("path", "g")
   .attr("class", "link")
   .attr("d", diagonal);
}
