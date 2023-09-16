
import { Burger, Button, Flex, Drawer, Title, Card, TextInput, Text, Modal, Center, Textarea } from "@mantine/core";
import { useDisclosure, useHotkeys } from "@mantine/hooks";
import { Carousel, Embla } from '@mantine/carousel';
import { useState } from "react";
import ReactCardFlip from 'react-card-flip';

const apiRootURL = 'http://127.0.0.1:8080';

type Card = {
  q: string,
  a: string
};

type Flashdeck = {
  name: string,
  cards: Card[]
};

const CardDisplay = (props: {card: Card, showAnswer: boolean}) => 
  <Card radius='xl' style={{width: '100%', height: '400px', boxShadow: '0px 20px 30px rgba(0, 0, 0, 0.2)'}}>
    <Flex justify='center' align='center' direction='column' style={{width: '100%', height: '100%'}}>
      <Title size='h3'>{props.showAnswer ? 'Answer' : 'Question'}</Title>
      <Text size='xl' style={{marginTop: '40px'}}>{props.showAnswer ? props.card.a : props.card.q}</Text>
    </Flex>
  </Card>;


function concat<T>(a: T[], b: T[]) {
  const res: T[] = [];
  a.forEach(x => res.push(x));
  b.forEach(x => res.push(x));
  return res;
}

async function post(url: string, data: any) {
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
  return response.json();
}

export default function Home() {
  const [decklistOpen, {toggle : decklistToggle, close: decklistClose}] = useDisclosure(false);
  const [decks, setDecks] = useState<Flashdeck[]>([
    {
      name: 'CS',
      cards: [
        {q: 'What is BFS', a: 'I don\'t know.'},
        {q: 'What is DFS', a: 'I don\'t know.'}
      ]
    },
    {
      name: 'Duck Anatomy',
      cards: [
        {q: 'How many legs do ducks have?', a: 'Researchers disagree, but estimates range from 12 to 16.'},
        {q: 'What do ducks do?', a: 'Ducks are dangerous and unpredictable beasts.'}
      ]
    }
  ]);
  const [openDeck, setOpenDeck] = useState(0);
  const deck = openDeck < decks.length ? decks[openDeck] : null; 
  const [openCard, setOpenCard] = useState(0);
  const card = (deck && openCard < deck?.cards.length) ? deck.cards[openCard] : null;
  const [showAnswer, {toggle: toggleAnswer, close: hideAnswer}] = useDisclosure(false);

  const wrapCardIdx = (idx: number) => deck ? ((idx % deck.cards.length + deck.cards.length) % deck.cards.length) : 0;
  const setCardIdx = (idx: number) => {setOpenCard(wrapCardIdx(idx)); hideAnswer()};

  const [createModalOpen, {open: openCreateModel, close: closeCreateModel}] = useDisclosure(false);
  const cardMode = !createModalOpen && !decklistOpen;

  const [embla, setEmbla] = useState<Embla | null>(null);

  const [notes, setNotes] = useState('');

  useHotkeys([
    ['Space', () => cardMode && toggleAnswer()],
    ['ArrowLeft', () => cardMode && [embla?.scrollPrev(), hideAnswer()]],
    ['ArrowRight', () => cardMode && [embla?.scrollNext(), hideAnswer()]],
    ['Tab', () => !createModalOpen && decklistToggle()]
  ]);

  const buttonGradient = {from: 'teal', to: 'lime', deg: 105};

  return <>
    <Burger opened={decklistOpen} onClick={decklistToggle}/>
    <Drawer opened={decklistOpen} onClose={decklistClose}>
      <Title size='h4'>Flashdecks</Title>
      {decks.map((deck, i) => <Button variant={i == openDeck ? 'light' : 'subtle'} key={i} style={{marginTop: '10px', display: 'block'}} onClick={() => {setOpenDeck(i); decklistClose(); hideAnswer(); setOpenCard(0);}}>{deck.name}</Button>)}
      <Button variant='gradient' style={{marginTop: '10px', display: 'block'}} gradient={buttonGradient} onClick={() => {decklistClose(); openCreateModel();}}>Create Flashdeck</Button>
    </Drawer>
    <Modal radius='lg' yOffset={150} opened={createModalOpen} onClose={closeCreateModel}>
      <Flex gap='md' justify='center' align='center' direction='column'>
        <Title size='h3'>Create Flashdeck</Title>
        <TextInput placeholder='Flashdeck Name'/>
        <Textarea value={notes} onChange={(e) => setNotes(e.currentTarget.value)} style={{width: '80%'}} placeholder='Your notes'/>
        <Button variant='gradient' gradient={buttonGradient} onClick={() => {
          post(apiRootURL + '/getCardsText', {
            text: notes
          }).then((deckData: {deck: {cards: {question: string, answer: string}[]}}) => {
            const deck: Flashdeck = {
              name: 'New Deck',
              cards: deckData.deck.cards.map(cardData => {return {q: cardData.question, a: cardData.answer};})
            };
            decks.push(deck);
            setDecks(decks);
          });
        }}>Generate! ✨</Button>
      </Flex>
    </Modal>
    {deck && <Flex justify='center' align='center' direction='column' style={{position: 'absolute', top: '0', left: '0', width: '100vw', height: '100vh', pointerEvents: 'none'}}>
      <Title style={{marginBottom: '50px'}}>{deck.name}</Title>
      <Carousel getEmblaApi={setEmbla} style={{overflow: 'inherit'}} slideGap='1000px' loop slideSize='70%' w='100%' withControls={false} mx='auto'>
        {concat(deck.cards, deck.cards).map((card, i) =>
          <Carousel.Slide>
            <ReactCardFlip flipSpeedBackToFront={0.4} flipSpeedFrontToBack={0.4} isFlipped={showAnswer} flipDirection='vertical'>
              <CardDisplay card={card} showAnswer={false}/>
              <CardDisplay card={card} showAnswer={true}/>
            </ReactCardFlip>
          </Carousel.Slide>)}
      </Carousel> 
    </Flex>}
  </>; 
}
