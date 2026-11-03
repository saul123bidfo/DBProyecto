// Separador para estos scripts controlados. Conserva ; dentro de triggers mediante DELIMITER.
export function splitSQL(source){let delimiter=';',buffer='',out=[];for(const line of source.split(/\r?\n/)){
 const directive=line.match(/^\s*DELIMITER\s+(\S+)\s*$/i);if(directive){if(buffer.trim())throw new Error('DELIMITER dentro de una sentencia');delimiter=directive[1];continue;}
 if(!buffer&&(/^\s*--/.test(line)||!line.trim()))continue;
 buffer+=line+'\n';if(buffer.trimEnd().endsWith(delimiter)){out.push(buffer.trimEnd().slice(0,-delimiter.length).trim());buffer='';}
 }if(buffer.trim())throw new Error('Sentencia SQL incompleta');return out;}
