# -*- coding: utf-8 -*-

""" Person super-entity

    @author: nursix
    @see: U{http://eden.sahanafoundation.org/wiki/BluePrintVITA}

"""

prefix = "pr"

# *****************************************************************************
# Person Entity
#
pr_pe_types = Storage(
    pr_person = T("Person"),
    pr_group = T("Group"),
    org_organisation = T("Organization"),
    org_office = T("Office"),
    dvi_body = T("Body")
)

resourcename = "pentity"
tablename = "pr_pentity"
table = super_entity(tablename, "pe_id", pr_pe_types,
                     Field("pe_label", length=128),
                     migrate=migrate)

s3xrc.model.configure(table, editable=False, deletable=False, listadd=False)

# -----------------------------------------------------------------------------
def shn_pentity_represent(id, default_label="[No ID Tag]"):

    """ Represent a Person Entity in option fields or list views """

    pe_str = T("None (no such record)")

    pe_table = db.pr_pentity
    pe = db(pe_table.pe_id == id).select(pe_table.instance_type,
                                         pe_table.pe_label,
                                         limitby=(0, 1)).first()
    if not pe:
        return pe_str

    instance_type = pe.instance_type
    instance_type_nice = pe_table.instance_type.represent(instance_type)

    table = db.get(instance_type, None)
    if not table:
        return pe_str

    label = pe.pe_label or default_label

    if instance_type == "pr_person":
        person = db(table.pe_id == id).select(
                    table.first_name, table.middle_name, table.last_name,
                    limitby=(0, 1)).first()
        if person:
            pe_str = "%s %s (%s)" % (
                vita.fullname(person), label, instance_type_nice
            )

    elif instance_type == "pr_group":
        group = db(table.pe_id == id).select(
                   table.name,
                   limitby=(0, 1)).first()
        if group:
            pe_str = "%s (%s)" % (
                group.name, instance_type_nice
            )

    elif instance_type == "org_organisation":
        organisation = db(table.pe_id == id).select(
                          table.name,
                          limitby=(0, 1)).first()
        if organisation:
            pe_str = "%s (%s)" % (
                organisation.name, instance_type_nice
            )

    elif instance_type == "org_office":
        office = db(table.pe_id == id).select(
                    table.name,
                    limitby=(0, 1)).first()
        if office:
            pe_str = "%s (%s)" % (
                office.name, instance_type_nice
            )

    else:
        pe_str = "[%s] (%s)" % (
            label,
            instance_type_nice
        )

    return pe_str


# -----------------------------------------------------------------------------
pe_label = S3ReusableField("pe_label", length=128,
                           label = T("ID Tag Number"),
                           requires = IS_NULL_OR(IS_NOT_ONE_OF(db,
                                      "pr_pentity.pe_label")))

# END
# *****************************************************************************
