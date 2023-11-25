from halpert import Sample, OdooSample
import halpert.functions.persona
import halpert.functions.wikipedia
import halpert.functions.odoo
import example.functions

samples = [
  Sample(
    name='Add two numbers',
    instructions='What is 1782937829 + 973912412?',
    functions=[example.functions.add],
    expected=Sample.Evaluation(
      functions=[example.functions.add.slug],
      quiz=[
        Sample.Evaluation.QuizItem(question='What is the first term?', answer='1782937829'),
        Sample.Evaluation.QuizItem(question='What is the second term?', answer='973912412'),
        Sample.Evaluation.QuizItem(question='What is the sum?', answer='2756850241'),
      ],
    )
  ),
  Sample(
    name='Search Wikipedia',
    instructions='Research the year 1092',
    functions=[
      halpert.functions.wikipedia.search,
      halpert.functions.wikipedia.read_page,
    ],
    expected=Sample.Evaluation(
      functions=[
        halpert.functions.wikipedia.search.slug,
        halpert.functions.wikipedia.read_page.slug,
      ],
      quiz=[
        Sample.Evaluation.QuizItem(question='What day of the week did the year start?', answer='Thursday'),
        Sample.Evaluation.QuizItem(question='What did England annex?', answer='Cumbria'),
      ],
    ),
  ),
  Sample(
    name='Message Friend',
    instructions='Send a message to your friend asking them how they are doing.',
    functions=[
      halpert.functions.persona.send_message_with_context('Say that you recently moved to San Francisco.'),
    ],
    expected=Sample.Evaluation(
      functions=[halpert.functions.persona.send_message.slug],
      quiz=[
        Sample.Evaluation.QuizItem(question='In what city does the friend live?', answer='San Francisco'),
      ],
    ),
  ),
  OdooSample(
    snapshot='cal',
  # Sample(
    name='List Calendar Events',
    instructions='List calendar events for November 2023',
    functions=[halpert.functions.odoo.calendar.list_events],
    expected=Sample.Evaluation(
      functions=[halpert.functions.odoo.calendar.list_events.slug],
      quiz=[
        Sample.Evaluation.QuizItem(question='Who is attending the event on the 22th?', answer='Administrator'),
      ],
    ),
  ),
]
