import arrow
from halpert import Function
from pydantic.dataclasses import dataclass
from pydantic import Field
from typing import List
from ...api import OdooAPI


@dataclass
class Input:
  start_date: str = Field(format='YYYY-MM-DD')
  end_date: str = Field(format='YYYY-MM-DD')


@dataclass
class Output:
  @dataclass
  class Event:
    @dataclass
    class User:
      id: int
      name: str
      is_organizer: bool

    id: int
    name: str
    description: str
    start: str
    end: str
    attendees: List[User]

  events: List[Event]


async def list_events_call(input: Input) -> Output:
  odoo = OdooAPI()
  results = odoo.search_read(
    'calendar.event',
    ['id', 'display_name', 'description', 'start', 'stop', 'partner_ids', 'allday'],
    [
      OdooAPI.SearchFilter('start', '>=', input.start_date),
      OdooAPI.SearchFilter('stop', '<', input.end_date),
    ]
  )

  return Output(events=[
    Output.Event(
      id=event['id'],
      name=event['display_name'],
      description=event['description'] or '', # consider stripping HTML
      start=event['start'] if not event['allday'] else arrow.get(event['start']).format('YYYY-MM-DD'),
      end=event['stop'] if not event['allday'] else arrow.get(event['stop']).format('YYYY-MM-DD'),
      attendees=[
        Output.Event.User(
          id=details.id,
          name=details.name,
          is_organizer=details.is_organizer,
        )
        for details in odoo.get_attendee_detail(event['partner_ids'], event['id'])
      ],
    )
    for event in results
  ])


list_events = Function(
  name='List Events',
  description='List events in Odoo Calendar',
  Input=Input,
  Output=Output,
  call=list_events_call,
)


if __name__ == '__main__':
  import asyncio
  events = asyncio.run(list_events.call(Input(
    start_date='2021-01-01',
    end_date='2024-12-31',
  )))

  print(events)
