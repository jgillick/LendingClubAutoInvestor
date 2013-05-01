/**
A simple node server to emulate LendingClub's APIs for unit testing
*/

var PORT = 7357;

var http = require('http'),
    url = require("url"),
    fs = require('fs'),
    util = require("util"),
    qs = require('querystring');

var authEmail = 'test@test.com',
    authPassword = 'testpassword',
    authName = 'Tester';

http.createServer(function (request, response) {
  var postData = "";

  /*
    GET requests
  */
  if (request.method == "GET") {
    // Start response. Assume everything is 200 and hunky-dory.
    response.writeHead(200, {
      'Content-Type': 'text/plain',
      'Access-Control-Allow-Origin': '*'
    });
    processGET(request, response);
  }

  /*
    POST requests
  */
  else if (request.method == "POST") {

    // Read data
    request.on("data", function(chunk) {
        postData += chunk;
    });

    // Process
    request.on("end", function() {
      postData = qs.parse(postData);
      processPOST(request, response, postData);
    });
  }

  // Everything else
  else {
    response.end();
  }

}).listen(PORT, '127.0.0.1');

/**
* Write a file to the output
*/
function outputFileAndEnd(filename, response){
  fs.readFile(__dirname +'/output/'+ filename, function (err, data) {
    if (!err) {
      response.write(data);
    }
    response.end();
  });
}

/**
* Output JSON error message
*/
function outputErrorJSON(msg, response){
  var error = {
    'result': 'error',
    'error': [ msg ]
  };
  response.write(JSON.stringify(error));
  response.end();
}

/**
* Process all GET requests
*/
function processGET(request, response){
  var path = url.parse(request.url).pathname,
      query = url.parse(request.url, true).query;

  switch(path){
    // Cash balance JSON
    case '/browse/cashBalanceAj.action':
      outputFileAndEnd('cashBalanceAj.json', response);
    break;
    // Porfolio list
    case '/data/portfolioManagement':
      if(query['method'] && query['method'] == 'getLCPortfolios'){
        outputFileAndEnd('portfolioManagement_getLCPortfolios.json', response);
      } else {
        response.write('Unknown method: '+ query['method']);
        response.end();
      }
    break;
    // Start order
    case '/portfolio/recommendPortfolio.action':
      // Empty response
      response.write("");
      response.end();
    break;
    // Place order and strut token
    case '/portfolio/placeOrder.action':
      outputFileAndEnd('placeOrder.html', response);
    break;
    default:
      response.write("Unknown GET: "+ path);
      response.end();
  }
}

/**
* Process all POST requests
*/
function processPOST(request, response, data){
  var path = url.parse(request.url).pathname,
      query = url.parse(request.url, true).query;
  switch(path){

    // Login - if the email and password match, set the cookie
    case '/account/login.action':
      if(data.login_email == authEmail && data.login_password == authPassword){
        response.writeHead(200, {
          'Set-Cookie': 'LC_FIRSTNAME='+ authName,
          'Content-Type': 'text/plain'
        });
      }
      response.write("Test Response");
      response.end();
    break;

    // Investment options
    case '/portfolio/lendingMatchOptionsV2.action':
      if(data.filter == 'default'){
        outputFileAndEnd('lendingMatchOptionsV2.json', response);
      } else{
        try {
          // Verify valid JSON filter
          var filters = JSON.parse(data.filter);
          if(typeof filters == 'object'
              && filters.length > 1
              && typeof filters[0]['m_id'] != 'undefined'){

            // Check Grade filters (only A, B and C should be selected, per autoinvestor_test.py)
            var foundGrade = false;
            for(var i = 0, len = filters.length; i < len; i++){
              var filter = filters[i],
                  values = filter['m_value'];

              if (filter['m_id'] == 10){
                foundGrade = true;

                for(var g = 0, glen = values.length; g < glen; g++){
                  var grade = values[g];

                  // If something other than A, B or C are present, the filter JSON is wrong
                  if (['A', 'B', 'C'].indexOf(grade['value']) < 0){
                    throw 'Grade "'+ grade['value'] +'"" should not be present in the filter. Only A, B and C.';
                  }
                }

              }
            }
            if (foundGrade == false){
              throw 'No grade filters defined';
            }

            // Everything checked out, give them the results!
            outputFileAndEnd('lendingMatchOptionsV2_filter.json', response);
          } else {
            outputErrorJSON('Invalid JSON filter: '+ data.filter, response);
          }
        } catch(e){
          outputErrorJSON(e.toString(), response);
        }
      }
    break;

    // Order confirmation
    case '/portfolio/orderConfirmed.action':
      outputFileAndEnd('orderConfirmed.html', response);
    break;

    // Assign to portfolio
    case '/data/portfolioManagement':
      if(query.method == 'addToLCPortfolio'){
        outputFileAndEnd('portfolioManagement_addToLCPortfolio.json', response);

      } else if(query.method == 'createLCPortfolio'){
        outputFileAndEnd('portfolioManagement_createLCPortfolio.json', response);

      } else {
        response.write('Unknown method: '+ query.method);
        response.end();
      }
    break;

    default:
      response.write('Unknown post: ' + path);
      response.end();
  }
}


util.log('Server running at http://127.0.0.1:'+ PORT +'/');