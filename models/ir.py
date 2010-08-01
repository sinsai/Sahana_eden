

table = db.define_table("ir_event",
        Field("reporter"),
        Field("contacts"),
        Field("shortDescription"),
        Field("comments"), 
        location_id,
        Field("reportTime"),
        Field("Photo", "upload"), 
   )

table = db.define_table("ir_eventstatus",
        Field("event_id", db.ir_event),
        Field("statusDescription"), 
   )

table.event_id.represent = lambda id: \
    db(db.ir_event.id == id).\
    select(db.ir_event.shortDescription, \
           limitby=(0,1)).first().shortDescription

module = "ir"
resource = "eventstatus"           
s3xrc.model.add_component(module,
                          resource,
                          mutiple=True,
                          joinby=dict(ir_event="event_id"),
                          deletable=True,
                          editable=True
                          )

   

 
   

 