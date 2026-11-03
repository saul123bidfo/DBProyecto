import 'dotenv/config';
import mysql from 'mysql2/promise';
export const connectionOptions={host:process.env.DB_HOST||'127.0.0.1',port:Number(process.env.DB_PORT||3306),user:process.env.DB_USER||'indrive_app',password:process.env.DB_PASSWORD||'',database:process.env.DB_NAME||'indrive_academico',charset:'utf8mb4',dateStrings:true,decimalNumbers:true,multipleStatements:false,connectTimeout:5000,...(process.env.DB_SOCKET?{socketPath:process.env.DB_SOCKET}:{})};
export const pool=mysql.createPool({...connectionOptions,connectionLimit:8});
export async function transaction(fn){const c=await pool.getConnection();try{await c.beginTransaction();const result=await fn(c);await c.commit();return result;}catch(e){await c.rollback();throw e;}finally{c.release();}}
