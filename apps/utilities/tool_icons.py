"""Tools hub tiles whose icon an admin can replace with an uploaded logo
(see ToolIcon). The default icon is the tile's original inline line-SVG —
trusted, code-authored markup rendered as-is by the {% tool_icon %} tag."""

# (key, section, tile name, default <svg> inner markup)
TOOL_ICONS = [
    ("saturation_temp", "Engineering", "SATURATION TEMP",
     '<path d="M12 14.5V5a2 2 0 10-4 0v9.5a4 4 0 104 0z"/><path d="M16 5h5M16 9h3M16 13h5"/>'),
    ("pdf_edit", "Documents", "PDF Edit",
     '<path d="M6 2h9l5 5v15H6z"/><path d="M15 2v5h5"/><path d="M9 17l1.5-4.5L15 8l1.5 1.5-4.5 4.5z"/>'),
    ("qr_code", "Documents", "QR Code",
     '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>'
     '<rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h3v3h-3zM20 14v3M14 20h3M20 20v.01"/>'),
    ("document_converter", "Documents", "Document Converter",
     '<path d="M4 4v6h6M20 20v-6h-6"/><path d="M5.5 15a7 7 0 0012.6 2.5M18.5 9A7 7 0 005.9 6.5"/>'),
    ("approve_doc", "Systems", "Approve Doc",
     '<path d="M6 2h9l5 5v15H6z"/><path d="M15 2v5h5"/><path d="M9.5 13.5l2 2 4-4.5"/>'),
    ("kace", "Systems", "KACE Systems",
     '<rect x="3" y="4" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/>'
     '<path d="M7 7.5h.01M7 16.5h.01"/>'),
    ("pscapa", "Systems", "PScapa",
     '<path d="M4 20V10M11 20V4M18 20v-7"/>'),
    ("temperature", "Calculators", "Temperature",
     '<path d="M12 14.5V5a2 2 0 10-4 0v9.5a4 4 0 104 0z"/>'),
    ("capacity", "Calculators", "Capacity",
     '<circle cx="12" cy="13" r="8"/><path d="M12 13l3-3M12 5V3"/>'),
    ("salary", "Calculators", "Salary",
     '<circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9.5c0-1.4 1.1-2.2 2.5-2.2s2.5.7 2.5 1.9c0 2.6-5 1.3-5 3.9 '
     '0 1.2 1.1 1.9 2.5 1.9s2.5-.8 2.5-2.2"/>'),
    ("unit", "Calculators", "Unit Converter",
     '<path d="M4 8h13M13 4l4 4-4 4"/><path d="M20 16H7M11 20l-4-4 4-4"/>'),
    ("percentage", "Calculators", "Percentage",
     '<circle cx="7" cy="7" r="2.5"/><circle cx="17" cy="17" r="2.5"/><path d="M18 6L6 18"/>'),
    ("datetime", "Calculators", "Date & Time",
     '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>'),
    ("oee", "Engineering", "OEE",
     '<path d="M4 18a8 8 0 1116 0"/><path d="M12 18l4-5"/>'),
    ("cycle", "Engineering", "Cycle Time",
     '<path d="M4 12a8 8 0 0114-5.3M20 12a8 8 0 01-14 5.3"/><path d="M18 3v4h-4M6 21v-4h4"/>'),
    ("power", "Engineering", "Power",
     '<path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z"/>'),
    ("pressure", "Engineering", "Pressure",
     '<circle cx="12" cy="13" r="8"/><path d="M12 13l3.5-4.5"/><circle cx="12" cy="13" r="1"/>'),
]

DEFAULT_SVGS = {key: svg for key, _section, _name, svg in TOOL_ICONS}
