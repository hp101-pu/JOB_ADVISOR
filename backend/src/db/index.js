import mongoose from "mongoose";


const connectDB=async()=>{
    try{
        console.log("URI",process.env.MONGO_URI);
        console.log(`${process.env.DB_NAME}`)
        await mongoose.connect(`${process.env.MONGO_URI}/${process.env.DB_NAME}`);
        console.log("Connected to MongoDB");
    }
    catch(error){
        console.log("ERROR",error)
        throw error
    }
    }
    export default connectDB;


