"""Platform-independent overlay layout logic (defaults, positioning)."""

DEFAULTS = {
    'monitor': 'follow_focus',
    'position': 'bottom_center',
    'margin': 80,
    'font_size': 16,
    'opacity': 0.85,
    'bg_color': '#1e1e1e',
    'text_color': '#ffffff',
}

POSITION_CALCULATORS = {
    'bottom_center': lambda m, ww, wh, mg: (
        m.work_x + (m.work_width - ww) // 2,
        m.work_y + m.work_height - wh - mg,
    ),
    'top_center': lambda m, ww, wh, mg: (
        m.work_x + (m.work_width - ww) // 2,
        m.work_y + mg,
    ),
    'bottom_left': lambda m, ww, wh, mg: (
        m.work_x + mg,
        m.work_y + m.work_height - wh - mg,
    ),
    'bottom_right': lambda m, ww, wh, mg: (
        m.work_x + m.work_width - ww - mg,
        m.work_y + m.work_height - wh - mg,
    ),
    'top_left': lambda m, ww, wh, mg: (
        m.work_x + mg,
        m.work_y + mg,
    ),
    'top_right': lambda m, ww, wh, mg: (
        m.work_x + m.work_width - ww - mg,
        m.work_y + mg,
    ),
    'center': lambda m, ww, wh, mg: (
        m.work_x + (m.work_width - ww) // 2,
        m.work_y + (m.work_height - wh) // 2,
    ),
}


def resolve_target_monitor(monitors_mod, config):
    mode = config.get('monitor', 'follow_focus')
    if mode == 'follow_focus':
        return monitors_mod.get_monitor_of_focused_window()
    if mode == 'cursor':
        return monitors_mod.get_monitor_at_cursor()
    if mode == 'primary':
        return monitors_mod.get_primary_monitor()
    if isinstance(mode, int):
        return monitors_mod.get_monitor_by_index(mode)
    return monitors_mod.get_primary_monitor()


def calculate_position(config, monitor, win_w, win_h):
    position = config.get('position', 'bottom_center')
    margin = config.get('margin', 80)
    calc = POSITION_CALCULATORS.get(position, POSITION_CALCULATORS['bottom_center'])
    return calc(monitor, win_w, win_h, margin)
