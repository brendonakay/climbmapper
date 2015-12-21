var express = require('express');
var router = express.Router();
var pg = require('pg');
var config = require('../config.js');

if(process.env.OPENSHIFT_POSTGRESQL_DB_URL){
	var dbUrl = process.env.OPENSHIFT_POSTGRESQL_DB_URL + "/climbmapper";
}
var conString = dbUrl || 'postgres://'+config.user_name+':'+config.password+'@localhost:5432/climbmapper';


exports.createUser = function(username, password) {
	var client = new pg.Client(conString);
   client.connect();
   
   console.log("creating user")
   var query = client.query("INSERT INTO appuser(username, password, displayname, email) VALUES ('"+username+"','"+password+"','"+username+"',null);");
   
   var userQuery = client.query("SELECT id, username, password, displayname, email FROM appuser WHERE username = '"+username+"';");
    
	var newUserObj = {
 			"id": 0, // TODO: this is fine for now  
 			"username": username, 
 			"displayname": username, 
 			"emails": ["email"] 
 			};
 			
    return newUserObj;
}

exports.updateProfile = function(res, user, mpuserkey, email, password) {
	
	var client = new pg.Client(conString);
   client.connect();
   
   var updateCallback = function(err, result) {
      res.redirect('/profile');
    }
   
   console.log("Updating user")
   if(mpuserkey.length > 0) {
   	client.query("UPDATE appuser SET mountainprojkey='"+mpuserkey+ "' WHERE id ='"+user.id.toString()+"';", updateCallback);
   }
   if(email.length > 0){
   	client.query("UPDATE appuser SET email='"+email+"' WHERE id ='"+user.id.toString()+"';", updateCallback);
   }
   if(password.length > 0){
   	client.query("UPDATE appuser SET password='"+password+"' WHERE id ='"+user.id.toString()+"';", updateCallback);
   }
   
}


exports.verifyPassword = function (password) {
	if(password.length < 1){
		return false;
	}
	
	return true;
}

exports.verifyUser = function (username, cb) {
	var client = new pg.Client(conString);
   client.connect();
   
	var query = client.query("SELECT id, username, password, displayname, email, mountainprojkey FROM appuser;");
   
    query.on('row', function(row, result) {
    	if (row) {
    	  rowJSON = { "id": row.id, "username": row.username, "password": row.password, "displayname": row.displayname, "emails": [row.email], "mountainprojkey": row.mountainprojkey };
        result.addRow(rowJSON);
      }
    })
    
    query.on("end", function (result) {
    		var records = result.rows;
			var theUser = null;
			
    		for (var i = 0; i < records.length; i++) {
		      var record = records[i];
		      if (record.username === username) {
		        return cb(null, record);
		      }
		   }
		    
		   return cb(null, false);
    })

}


exports.findByUsername = function(username, cb) {
  process.nextTick(function() { 	  
  	 var client = new pg.Client(conString);
    client.connect();
    
    var query = client.query("SELECT id, username, password, displayname, email, mountainprojkey FROM appuser;");
   
    query.on('row', function(row, result) {
    	  
        if (row) {
        		rowJSON = { "id": row.id, "username": row.username, "password": row.password, "displayname": row.displayname, "emails": [row.email], "mountainprojkey": row.mountainprojkey };
        		result.addRow(rowJSON);
        }
    })
    
    query.on("end", function (result) {
    		
    		var records = result.rows;
    
    		for (var i = 0; i < records.length; i++) {
		      var record = records[i];
		      if (record.username === username) {
		        return cb(null, record);
		      }
		    }

    		return cb(null, null);
    })

  });
}


/*exports.findByEmail = function(email, cb) {
  process.nextTick(function() { 	  
  	 var client = new pg.Client(conString);
    client.connect();
    
    var query = client.query("SELECT id, username, password, displayname, email FROM appuser;");
   
    query.on('row', function(row, result) {
    	  
        if (row) {
        		rowJSON = { "id": row.id, "username": row.username, "password": row.password, "displayname": row.displayname, "emails": [row.email] };
        		result.addRow(rowJSON);
        }
    })
    
    query.on("end", function (result) {
    		
    		var records = result.rows;
    		
    		for (var i = 0, len = records.length; i < len; i++) {
		      var record = records[i];
		      console.log(record.emails[0], " - ", email)
		      if (record.emails[0] === email) {
		        return cb(null, record);
		      }
		      else{
					console.log("nope")		      
		      }
		    }

    		return cb(null, null);
    })

  });
}
*/

exports.findById = function(id, cb) {

  process.nextTick(function() {  
  	 var client = new pg.Client(conString);
    client.connect();
    
    var query = client.query("SELECT id, username, password, displayname, email, mountainprojkey FROM appuser;");
   
    query.on('row', function(row, result) {
        if (row) {
        		rowJSON = { "id": row.id, "username": row.username, "password": row.password, "displayname": row.displayname, "emails": [row.email], "mountainprojkey": row.mountainprojkey };
        		result.addRow(rowJSON);
        }
    })
    
    query.on("end", function (result) { 		
    		var records = result.rows; 		
    		for (var i = 0, len = records.length; i < len; i++) {
		      var record = records[i];
		      if (record.id === id) {
		        return cb(null, record);
		      }
		    }

    		return cb(null, null);
    })

  });
}
