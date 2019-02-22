var http = require('http');

var handleRequest = function(request, response) {
  console.log('Received request for URL: ' + request.url);
  response.writeHead(200);
  response.end('Hello World! This message comes from pod: ' + process.env.POD_NAME + '(' + process.env.POD_IP + ')');
};
var www = http.createServer(handleRequest);
www.listen(8888);