from enum import Enum

class Role(Enum):
    tank = 'Tank'
    healer = 'Healer'
    dps = 'DPS'
    clear_role = 'Clear Role'

Role = Enum('Role', [
    ('tank', 'Tank'),
    ('healer', 'Healer'),
    ('dps', 'DPS'),
    ('clear_role', 'Clear Role')
])