// Restricciones de unicidad (crean también un índice) e índices auxiliares.
CREATE CONSTRAINT usuario_id      IF NOT EXISTS FOR (u:Usuario)   REQUIRE u.id IS UNIQUE;
CREATE CONSTRAINT usuario_email   IF NOT EXISTS FOR (u:Usuario)   REQUIRE u.email IS UNIQUE;
CREATE CONSTRAINT empresa_id      IF NOT EXISTS FOR (e:Empresa)   REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT empresa_nombre  IF NOT EXISTS FOR (e:Empresa)   REQUIRE e.nombre IS UNIQUE;
CREATE CONSTRAINT habilidad_clave IF NOT EXISTS FOR (h:Habilidad) REQUIRE h.clave IS UNIQUE;
CREATE CONSTRAINT proyecto_id     IF NOT EXISTS FOR (p:Proyecto)  REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT oferta_id       IF NOT EXISTS FOR (o:Oferta)    REQUIRE o.id IS UNIQUE;
CREATE INDEX usuario_nombre IF NOT EXISTS FOR (u:Usuario) ON (u.nombre);
CREATE INDEX oferta_estado  IF NOT EXISTS FOR (o:Oferta)  ON (o.estado);
