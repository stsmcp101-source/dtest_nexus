"""Internal menu logos and their original built-in icons."""

INTERNAL_ICONS = [
    ('training_history', "รายการ", 'External Training History', '<path d="M12 14l9-5-9-5-9 5 9 5z"/><path d="M3 9v6c0 1.5 4 3 9 3s9-1.5 9-3V9"/>'),
    ('test_room_damage', "รายการ", 'History Test room Damage', '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 10h18"/><path d="M9 15l2.5 2.5L15 13"/>'),
    ('spare_parts', "รายการ", 'Spare part', '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09a1.65 1.65 0 00-1-1.51 1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09a1.65 1.65 0 001.51-1 1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/>'),
    ('test_unit_control', "รายการ", 'Test Unit Control', '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M8 10v4M12 8v8M16 10v4"/>'),
    ('pipe_stock', "รายการ", 'Pipe Stock', '<path d="M4 8h9a4 4 0 010 8H9"/><circle cx="4" cy="8" r="2"/><circle cx="9" cy="16" r="2"/>'),
    ('refrigerant_stock', "รายการ", 'Refrigerant Stock', '<path d="M10 3h4v4l4 8a3 3 0 01-3 5H9a3 3 0 01-3-5l4-8V3z"/><path d="M8.5 15h7"/>'),
    ('tape_stock', "รายการ", 'Tape Stock', '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.5"/>'),
    ('paper_stock', "รายการ", 'Paper Stock', '<path d="M7 3h8l4 4v14H7z"/><path d="M15 3v4h4"/><path d="M10 12h6M10 16h6"/>'),
    ('other_stock', "รายการ", 'Other Stock', '<path d="M3 8l9-5 9 5-9 5-9-5z"/><path d="M3 8v9l9 5 9-5V8"/><path d="M12 13v9"/>'),
]

DEFAULT_SVGS = {key: svg for key, _section, _name, svg in INTERNAL_ICONS}
