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
    return cls(
      id=data['id'],
      name=data['display_name'],
      description=data['description'] or '', # consider stripping HTML
      start=data['start'] if not data['allday'] else arrow.get(data['start']).format('YYYY-MM-DD'),
      end=data['stop'] if not data['allday'] else arrow.get(data['stop']).format('YYYY-MM-DD'),
      attendees=[
        Event.User(
          id=details.id,
          name=details.name,
          is_organizer=details.is_organizer,
        )
        for details in odoo.get_attendee_detail(data['partner_ids'], data['id'])
      ],
    )
