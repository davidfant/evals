import arrow
from typing import List, Dict
from pydantic import BaseModel
from ...api import OdooAPI


class Event(BaseModel):
  class User(BaseModel):
    id: int
    name: str
    is_organizer: bool

  id: int
  name: str
  description: str
  start: str
  end: str
  attendees: List[User]

  @classmethod
  def from_api(cls, data: Dict, odoo: OdooAPI):
    format = 'YYYY-MM-DD HH:mm' if not data['allday'] else 'YYYY-MM-DD'
    return cls(
      id=data['id'],
      name=data['display_name'],
      description=data['description'] or '', # consider stripping HTML
      start=arrow.get(data['start']).format(format),
      end=arrow.get(data['stop']).format(format),
      attendees=[
        Event.User(
          id=details.id,
          name=details.name,
          is_organizer=details.is_organizer,
        )
        for details in odoo.get_attendee_detail(data['partner_ids'], data['id'])
      ],
    )
