import cpp

from Struct t, int size
where
	size = t.getSize() and size != 0

select t.getName() as structname, size, t.getDefinitionLocation() as file
