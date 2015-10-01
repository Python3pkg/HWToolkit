function doesRectangleOverlap(a, b) {
	  return (Math.abs(a.x - b.x) * 2 < (a.width + b.width)) &&
	         (Math.abs(a.y - b.y) * 2 < (a.height + b.height));
}

// used for collision detection, and keep out behavior of nodes
function nodeColisionResolver(node) {
	  var nx1, nx2, ny1, ny2, padding;
	  padding = 32;
	  function x2(node){
		  return node.x + node.width; 
	  }
	  function y2(node){
		  return node.y + node.height; 
	  }
	  nx1 = node.x - padding;
	  nx2 = x2(node) + padding;
	  ny1 = node.y - padding;
	  ny2 = y2(node.y) + padding;
	  
	  
	  return function(quad, x1, y1, x2, y2) {
	    var dx, dy;
		function x2(node){
		 return node.x + node.width; 
		}
		function y2(node){
		 return node.y + node.height; 
		}
	    if (quad.point && (quad.point !== node)) {
	      if (doesRectangleOverlap(node, quad.point)) {
	        dx = Math.min(x2(node)- quad.point.x, x2(quad.point) - node.x) / 2;
	        node.x -= dx;
	        quad.point.x -= dx;
	        dy = Math.min(y2(node) - quad.point.y,y2(quad.point) - node.y) / 2;
	        node.y -= dy;
	        quad.point.y += dy;
	      }
	    }
	    return x1 > nx2 || x2 < nx1 || y1 > ny2 || y2 < ny1;
	  };
};


function netMouseOver() {
	var net = d3.select(this)[0][0].__data__.net;
	d3.selectAll(".link")
	  .classed("link-selected", 
			  function(d){
		  			return d.net === net
	  		  });
}
function netMouseOut() {
	d3.selectAll(".link")
	  .classed("link-selected", false);
}

function redraw(){ //main function for renderign components layout
	var place = d3.select("#chartWraper").node().getBoundingClientRect();
	d3.select("#chartWraper").selectAll("svg").remove(); // delete old on redraw
	
	//force for self organizing of diagram
	var force = d3.layout.force()
		.gravity(.00)
		.distance(150)
		.charge(-2000)
		.size([place.width, place.height])
		.nodes(nodes)
		.links(links)
		.start();
	
	var svg = d3.select("#chartWraper").append("svg");
	var svgGroup= svg.append("g"); // because of zooming/moving


	var wrap = svgGroup.selectAll("g")
		.data(nodes)
		.enter()
		.append("g")
	    .classed({"component": true})
	    .attr("transform", function(d) {
	    	return "translate(" + [ d.x,d.y ] + ")"; 
	    })
	    .call(force.drag); //component dragging
	
	// background
	wrap.append("rect")
	    .attr("rx", 5) // this make rounded corners
	    .attr("ry", 5)
	    .attr("width", function(d) { return d.width})
	    .attr("height", function(d) { return d.height});
	
	// component name
	wrap.append('text')
		.attr("y", 10)
		.text(function(d) {
		    return d.name;
		});

	
	// input port wraps
	var port_inputs = wrap.append("g")
		.attr("transform", function(d) { 
			return "translate(" + 0 + "," + 3*portHeight + ")"; 
		})
		.selectAll("g .port-input")
		.data(function (d){
			return d.inputs;
		})
		.enter()
		.append('g')
		.classed({"port-input": true});
	
	// input port icon
	port_inputs.append("image")
		.attr("xlink:href", function(d) { 
			return "/static/hls/connections/arrow_right.ico"; 
		})
		.attr("y", function(d, i){
			return (i-1)*portHeight;
		})
		.attr("width", 10)
		.attr("height", portHeight);
	
	// portName text
	port_inputs.append('text')
		.attr("x", 10)
		.attr("y", function(d, i){
			return i*portHeight;
		})
		.attr("height", portHeight)
		.text(function(portName) { 
			return portName; 
		});
	
	// output port wraps
	var port_out = wrap.append("g")
		.attr("transform", function(d) { 
			var componentWidth = d3.select(this).node().parentNode.getBoundingClientRect().width
			return "translate(" + componentWidth/2 + "," + 3*portHeight + ")"; 
		})
		.selectAll("g .port-group")
		.data(function (d){
			return d.outputs;
		})
		.enter()
		.append('g')
		.classed({"port-output": true});
	
	// portName text
	port_out.append('text')
		.attr("x", 10)
		.attr("y", function(d, i){
			return i*portHeight;
		})
		.attr("height", portHeight)
		.text(function(portName) { 
			return portName; 
		});
	
    var link = svgGroup.selectAll(".link")
    	.data(links)
    	.enter()
    	.append("path")
    	.classed({"link": true})
    	.on("mouseover", netMouseOver)
    	.on("mouseout", netMouseOut);
	
    function update(){
		wrap.attr("transform", function (d) {
            return "translate(" + d.x + "," + d.y + ")";
        });
    	link.attr("d", function (d) {
            var sx = d.source.x + d.source.width;
            var sy = d.source.y + portsOffset + d.sourceIndex * portHeight;
            var tx = d.target.x;
            var ty = d.target.y + portsOffset + d.targetIndex * portHeight;
            return "M" + sx + "," + sy + " L " + tx + "," + ty;
        });
	};
	
    force.on("tick", function () {
    	var q = d3.geom.quadtree(nodes),
            i = 0,
            n = nodes.length;
    
    	while (++i < n) 
    		q.visit(nodeColisionResolver(nodes[i]));
    	
    	update();
    });
    
    //update();
    
    // define the zoomListener which calls the zoom function on the "zoom" event constrained within the scaleExtents
    var zoomListener = d3.behavior.zoom().scaleExtent([0.1, 3]).on("zoom",  
    		function () {
    			svgGroup.attr("transform", "translate(" + d3.event.translate + ")scale(" + d3.event.scale + ")");
    		}
    );
    svg.call(zoomListener);
}