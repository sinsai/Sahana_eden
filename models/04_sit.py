# -*- coding: utf-8 -*-

""" S3 Situations

    @author: nursix

"""

module = "sit"

# Situation super-entity
situation_types = Storage(
    irs_incident = T("Incident"),
    rms_req = T("Request")
)

resource = "situation"
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                        Field("sit_id", "id"),
                        Field("sit_type"),
                        Field("uuid", length=128),
                        Field("datetime", "datetime"),
                        location_id(),
                        migrate=migrate, *s3_deletion_status())


table.sit_type.writable = False
table.sit_type.represent = lambda opt: situation_types.get(opt, opt)
table.uuid.writable = False

sit_id = S3ReusableField("sit_id", db.sit_situation,
                         requires = IS_NULL_OR(IS_ONE_OF(db, "sit_situation.id", "%(sit_id)s", orderby="sit_situation.sit_id")),
                         represent = lambda id: id and str(id) or NONE,
                         readable = False,
                         writable = False,
                         ondelete = "RESTRICT")

# -----------------------------------------------------------------------------
def s3_situation_ondelete(record):

    uid = record.get("uuid", None)

    if uid:

        situation = db.sit_situation
        db(situation.uuid == uid).update(deleted=True)

    return True


# -----------------------------------------------------------------------------
def s3_situation_onaccept(form, table=None):

    if not "uuid" in table.fields or "id" not in form.vars:
        return False

    id = form.vars.id

    if "datetime" in table.fields:
        fields = [table.id, table.uuid, table.datetime]
    elif "timestmp" in table.fields:
        fields = [table.id, table.uuid, table.timestmp]
    else:
        fields = [table.id, table.uuid]
    if "location_id" in table.fields:
        fields.append(table.location_id)
    if "deleted" in table.fields:
        fields.append(table.deleted)
    record = db(table.id == id).select(limitby=(0, 1), *fields).first()

    if record:

        situation = db.sit_situation
        uid = record.uuid

        sit = db(situation.uuid == uid).select(situation.sit_id, limitby=(0, 1)).first()
        if sit:
            values = dict(sit_type=table._tablename,
                          uuid=record.uuid,
                          deleted=record.deleted)
            if "datetime" in record:
                values.update(datetime = record.datetime)
            elif "timestmp" in record:
                values.update(datetime = record.timestmp)
            if "location_id" in record:
                values.update(location_id = record.location_id)
            db(situation.uuid == uid).update(**values)
        else:
            values = dict(sit_type=table._tablename,
                          uuid=record.uuid,
                          deleted=False)
            if "datetime" in record:
                values.update(datetime = record.datetime)
            elif "timestmp" in record:
                values.update(datetime = record.timestmp)
            if "location_id" in record:
                values.update(location_id = record.location_id)
            sit_id = situation.insert(**values)
            db(table.id == id).update(sit_id=sit_id)

        return True

    else:
        return False

# -----------------------------------------------------------------------------
