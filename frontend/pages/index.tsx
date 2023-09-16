
import { Burger, Button, Flex, Drawer, Title, Card, TextInput, Text, Modal, Loader, Textarea, SegmentedControl, FileInput } from "@mantine/core";
import { useDisclosure, useHotkeys } from "@mantine/hooks";
import { Carousel, Embla } from '@mantine/carousel';
import { useEffect, useState } from "react";
import ReactCardFlip from 'react-card-flip';
import confetti from 'canvas-confetti'; 

const apiRootURL = 'http://127.0.0.1:8080';

type Card = {
  question: string,
  answer: string
};

type Flashdeck = {
  title: string,
  cards: Card[]
};

type GeneratorState = 'input' | 'generating' | 'done';
type InputSource = 'notes' | 'ocr' | 'webscrape';

const CardDisplay = (props: {card: Card, showAnswer: boolean}) => 
  <Card radius='xl' style={{width: '100%', height: '400px', boxShadow: '0px 20px 30px rgba(0, 0, 0, 0.2)'}}>
    <Flex justify='center' align='center' direction='column' style={{width: '100%', height: '100%'}}>
      <Title size='h3'>{props.showAnswer ? 'Answer' : 'Question'}</Title>
      <Text size='xl' style={{marginTop: '40px'}}>{props.showAnswer ? props.card.answer : props.card.question}</Text>
    </Flex>
  </Card>;


function concat<T>(a: T[], b: T[]) {
  const res: T[] = [];
  a.forEach(x => res.push(x));
  b.forEach(x => res.push(x));
  return res;
}

async function get(url: string) {
  const response = await fetch(url);
  return response.json();
}

async function post(url: string, data: any) {
  let formData = null;
  if(data instanceof File) {
    formData = new FormData(); 
    formData.append('file', data);
  }
  const response = await fetch(url, {
    method: 'POST',
    headers: (data instanceof File) ? {} : {'Content-Type': 'application/json'},
    body: data instanceof File ? formData : JSON.stringify(data),
  });
  return response.json();
}

export default function Home() {
  const [decklistOpen, {toggle : decklistToggle, close: decklistClose}] = useDisclosure(false);
  const [decks, setDecks] = useState<Flashdeck[]>([]);
  const [openDeck, setOpenDeck] = useState(0);
  const deck = openDeck < decks.length ? decks[openDeck] : null; 
  const [showAnswer, {toggle: toggleAnswer, close: hideAnswer}] = useDisclosure(false);

  const [createModalOpen, {open: openCreateModel, close: closeCreateModel}] = useDisclosure(false);
  const [generatorState, setGeneratorState] = useState<GeneratorState>('input');
  const cardMode = !createModalOpen && !decklistOpen;

  const [embla, setEmbla] = useState<Embla | null>(null);

  const [deckTitle, setDeckTitle] = useState('');
  const [inputSource, setInputSource] = useState<InputSource>('notes');
  const [notes, setNotes] = useState('');
  const [photo, setPhoto] = useState<File | null>(null);
  const [url, setUrl] = useState('');

  useEffect(() => {
    get(apiRootURL + '/decks').then((data) => {
      setDecks(data);
    });
  }, []);

  const clearCreateModalParams = () => {
    setDeckTitle('');
    setInputSource('notes');
    setNotes('');
    setPhoto(null);
    setGeneratorState('input');
    setUrl('');
  };

  const inputTypeToEndpoint = {
    'notes': '/generate',
    'ocr': '/img_generate',
    'webscrape': '/webscrape_generate'
  };

  const getGenerateRequestData = () => {
    switch(inputSource) {
      case 'notes':
        return {text: notes};
      case 'ocr':
        return photo;
      case 'webscrape':
        return {url: url};
    }
  };

  useHotkeys([
    ['Space', () => cardMode && toggleAnswer()],
    ['ArrowLeft', () => cardMode && [embla?.scrollPrev(), hideAnswer()]],
    ['ArrowRight', () => cardMode && [embla?.scrollNext(), hideAnswer()]],
    ['Tab', () => !createModalOpen && decklistToggle()]
  ]);

  const buttonGradient = {from: 'teal', to: 'lime', deg: 105};

  const createModalSourceUI = () => {
    switch(inputSource) {
      case 'notes':
        return <Textarea value={notes} onChange={(e) => setNotes(e.currentTarget.value)} style={{width: '80%'}} placeholder='Your notes'/>;
      case 'ocr':
        return <FileInput accept='image/*' placeholder='Select Photo...' value={photo} onChange={(file) => setPhoto(file)}/>
      case 'webscrape':
        return <TextInput placeholder='URL' value={url} onChange={(e) => setUrl(e.currentTarget.value)}/>
    }
  }

  const createModalInputUI = () => <>
      <TextInput value={deckTitle} onChange={(e) => setDeckTitle(e.currentTarget.value)} placeholder='Flashdeck Name'/>
      <SegmentedControl value={inputSource} onChange={(value) => setInputSource(value as InputSource)} data={[
        {label: 'Text Notes', value: 'notes'},
        {label: 'Photo', value: 'ocr'},
        {label: 'Website', value: 'webscrape'}
      ]}/>
      {createModalSourceUI()}
      <Button variant='gradient' gradient={buttonGradient} onClick={() => {
      setGeneratorState('generating');
      post(apiRootURL + inputTypeToEndpoint[inputSource], getGenerateRequestData()) 
      .then((deckData: {deck: {title: string, cards: {question: string, answer: string}[]}}) => {
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.4 }
        });
        setGeneratorState('done');
        const deck: Flashdeck = {
          title: deckTitle, 
          cards: deckData.deck.cards.map(cardData => {return {question: cardData.question, answer: cardData.answer};})
        };
        post(apiRootURL + '/decks', deck);
        decks.push(deck);
        setDecks(decks);
      });
    }}>Generate! ✨</Button>
  </>;

  const createModalGeneratingUI = () => <>
    <Loader color="lime" variant="bars"/>
  </>;

  const createModalDoneUI = () => <>
    ✨ Flashdeck generated! ✨ 
  </>;

  return <>
    <Burger opened={decklistOpen} onClick={decklistToggle}/>
    <Drawer opened={decklistOpen} onClose={decklistClose}>
      <Title size='h4'>Flashdecks</Title>
      {decks.map((deck, i) => <Button variant={i == openDeck ? 'light' : 'subtle'} key={i} style={{marginTop: '10px', display: 'block'}} onClick={() => {setOpenDeck(i); decklistClose(); hideAnswer(); embla?.scrollTo(0, true)}}>{deck.title}</Button>)}
      <Button variant='gradient' style={{marginTop: '10px', display: 'block'}} gradient={buttonGradient} onClick={() => {decklistClose(); openCreateModel(); clearCreateModalParams();}}>Create Flashdeck</Button>
    </Drawer>
    <Modal radius='lg' yOffset={150} opened={createModalOpen} onClose={closeCreateModel}>
      <Flex style={{marginBottom: '30px'}} gap='md' justify='center' align='center' direction='column'>
        <Title size='h3'>Create Flashdeck</Title>
        {generatorState == 'input' ? createModalInputUI() : (generatorState == 'generating' ? createModalGeneratingUI() : createModalDoneUI())}
      </Flex>
    </Modal>
    {deck && <Flex justify='center' align='center' direction='column' style={{position: 'absolute', top: '0', left: '0', width: '100vw', height: '100vh', pointerEvents: 'none'}}>
      <Title style={{marginBottom: '50px'}}>{deck.title}</Title>
      <Carousel getEmblaApi={setEmbla} style={{overflow: 'inherit'}} slideGap='1000px' loop slideSize='70%' w='100%' withControls={false} mx='auto'>
        {concat(deck.cards, deck.cards).map((card, i) =>
          <Carousel.Slide>
            <ReactCardFlip flipSpeedBackToFront={0.3} flipSpeedFrontToBack={0.3} isFlipped={showAnswer} flipDirection='vertical'>
              <CardDisplay card={card} showAnswer={false}/>
              <CardDisplay card={card} showAnswer={true}/>
            </ReactCardFlip>
          </Carousel.Slide>)}
      </Carousel> 
    </Flex>}
  </>; 
}
