//lets require/import the mongodb native drivers.

var mongodb = require('mongodb');

//We need to work with "MongoClient" interface in order to connect to a mongodb server.
var MongoClient = mongodb.MongoClient;

// Connection URL. This is where your mongodb server is running.
var url = 'mongodb://heroku_bnjrx3s8:ra6mg5rivid9dm2r38u0nvr74g@ds019085-a0.mlab.com:19085,ds019085-a1.mlab.com:19085/heroku_bnjrx3s8?replicaSet=rs-ds019085';

// Use connect method to connect to the Server
MongoClient.connect(url, function (err, db) {
  if (err) {
    console.log('Unable to connect to the mongoDB server. Error:', err);
  } else {
    //HURRAY!! We are connected. :)
    console.log('Connection established to', url);

    // do some work here with the database.

    //Close connection
    db.close();
  }
});