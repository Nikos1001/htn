
import { Burger, Button, Flex, Drawer, Title, Card } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useState } from "react";

type Flashdeck = {
  name: string,
  cards: {
    q: string,
    a: string
  }[]
};

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

  return <>
    <Burger opened={decklistOpen} onClick={decklistToggle}/>
    <Drawer opened={decklistOpen} onClose={decklistClose}>
      <Title size='h4'>Flashdecks</Title>
      {decks.map((deck, i) => <Button variant={i == openDeck ? 'light' : 'subtle'} key={i} style={{marginTop: '10px', display: 'block'}} onClick={() => {setOpenDeck(i); decklistClose();}}>{deck.name}</Button>)}
      <Button variant='gradient' style={{marginTop: '10px', display: 'block'}} gradient={{from: 'teal', to: 'lime', deg: 105}}>New Flashdeck</Button>
    </Drawer>
    <Flex justify='center' align='center' direction='column' style={{position: 'absolute', top: '0', left: '0', width: '100vw', height: '100vh', pointerEvents: 'none'}}>
      <Title style={{marginBottom: '50px'}}>{decks[openDeck].name}</Title>
      <Card radius='xl' style={{width: '600px', height: '400px'}}>
        Hey hey
      </Card> 
    </Flex>
  </>; 
}
