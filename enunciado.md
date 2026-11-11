TITULO

Diseño e implementación de una aplicación basada en base de datos de grafos para la   gestión y análisis de relaciones en una red profesional.

OBJETIVOS

1.	Afianzar los conocimientos de Diseño y modelamiento de bases de datos no relacionales.

2.	Demostrar la utilidad de las bases de datos de grafos en escenarios donde predominan las relaciones múltiples y dinámicas entre entidades, evidenciando sus ventajas frente a modelos tradicionales en tareas de análisis de redes y recomendación.

ENUNCIADO

En la actualidad, muchas aplicaciones requieren almacenar y consultar información altamente interconectada, donde las relaciones entre los datos son tan importantes como los datos mismos. En este contexto, las bases de datos de grafos representan una solución eficiente para modelar estructuras complejas, lo que permite recorrer conexiones sin las costosas operaciones de JOIN que exige el modelo relacional cuando la profundidad de la consulta crece.

A partir de esta necesidad, se plantea el desarrollo de una aplicación orientada a la gestión de una red profesional, en la cual se puedan representar entidades como usuarios, empresas, habilidades, proyectos y ofertas laborales, así como las relaciones existentes entre ellas. El sistema deberá permitir el registro, almacenamiento, consulta y análisis de dichas conexiones, con el fin de facilitar procesos de búsqueda, recomendación e identificación de oportunidades laborales o colaborativas. 

La aplicación deberá implementarse utilizando una base de datos de grafos, de manera que se aprovechen sus capacidades para modelar relaciones complejas y ejecutar consultas como detección de conexiones entre usuarios, identificación de habilidades compartidas, recomendaciones de contactos y vinculación entre candidatos y vacantes. Adicionalmente, como componente de investigación, los estudiantes deberán explicar en qué escenarios el modelo de grafos supera al relacional y en cuáles no.

La aplicación debe permitir:

•	Registrar, consultar, actualizar y eliminar (CRUD) usuarios con información personal y profesional.

•	Relacionar usuarios con otros usuarios mediante conexiones profesionales.

•	Vincular usuarios con habilidades, empresas y proyectos.

•	Registrar empresas y sus ofertas laborales que publican.

•	Relacionar ofertas laborales con las habilidades requeridas.

•	Permitir que un usuario se postule a una oferta.

•	Consultar caminos y conexiones entre usuarios, empresas y oportunidades laborales.

•	Generar recomendaciones de contactos, empleos o colaboradores a partir de la estructura del grafo.

•	Mostrar un panel de analítica: usuarios más influyentes, comunidades detectadas y habilidades más demandadas.

El sistema debe aprovechar las ventajas de una base de datos de grafos para responder preguntas como:

•	¿Qué usuarios tienen habilidades similares?

•	¿Qué contactos en común existen entre dos profesionales?

•	¿Cuál es la ruta más corta entre un usuario y una empresa?

•	¿Qué candidatos podrían recomendarse para una oferta según sus conexiones y competencias?

•	¿Qué proyectos comparten tecnologías o miembros relacionados?

•	¿Qué habilidades son las más demandadas en las ofertas?

Posibles entidades del grafo:

Nodo		Descripción

Usuario	Persona registrada en la plataforma

Empresa	Organización o compañía

Habilidad	Competencia o conocimiento

Proyecto	Trabajo o iniciativa desarrollada

Oferta		Vacante laboral

Posibles relaciones:

Relación		Significado

CONECTA_CON	Relación entre usuarios

TRABAJA_EN		Usuario vinculado a empresa

TIENE_HABILIDAD	Usuario posee una habilidad

PARTICIPA_EN		Usuario participa en un proyecto

PUBLICA		Empresa pública una oferta

REQUIERE		Oferta que requiere una habilidad

POSTULA_A		Postulación a una vacante

