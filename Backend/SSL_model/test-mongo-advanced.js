
const { MongoClient } = require('mongodb');
require('dotenv').config();

const uri = process.env.MONGODB_URI;
console.log('Connecting to:', uri.replace(/:[^:]*@/, ':****@'));

const client = new MongoClient(uri, {
    connectTimeoutMS: 5000,
    serverSelectionTimeoutMS: 5000
});

async function testConnection() {
    try {
        await client.connect();
        console.log('✅ Connected successfully to MongoDB!');

        // List databases to verify permissions
        const dbs = await client.db().admin().listDatabases();
        console.log('Available databases:', dbs.databases.map(db => db.name));

        await client.close();
    } catch (err) {
        console.error('❌ Connection failed!');
        console.error('Error name:', err.name);
        console.error('Error message:', err.message);

        if (err.message.includes('Authentication failed')) {
            console.error('\n🔐 AUTHENTICATION ERROR:');
            console.error('   - Check username and password are correct');
            console.error('   - Password has no special characters needing encoding');
            console.error('   - User has access to the database');
        } else if (err.message.includes('ENOTFOUND')) {
            console.error('\n🌐 DNS ERROR:');
            console.error('   - Check your internet connection');
            console.error('   - Try flushing DNS: ipconfig /flushdns');
            console.error('   - Try using Google DNS: 8.8.8.8');
        } else if (err.message.includes('timed out')) {
            console.error('\n⏱️  TIMEOUT ERROR:');
            console.error('   - Your IP might not be whitelisted in MongoDB Atlas');
            console.error('   - Check network/firewall settings');
            console.error('   - Verify cluster is running in Atlas');
        }
    }
}

testConnection();


