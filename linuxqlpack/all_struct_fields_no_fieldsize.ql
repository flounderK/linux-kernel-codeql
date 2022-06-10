import cpp

from Struct t, Field field, string structname
where
	t.getSize() != 0 and
	structname = t.getName() and
	field = t.getAField()

select  structname, t.getSize() as structsize, field.getType() as type, field.getName() as fieldname, field.getByteOffset() as offset

