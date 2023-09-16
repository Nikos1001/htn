
type Card = {
  question: string,
  answer: string
};

type Flashdeck = {
  title: string,
  text: string,
  cards: Card[]
};

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

const apiRootURL = () => {
  return 'http://' + window.location.hostname + ':3001';
}; 

export { get, post, apiRootURL };
export type { Flashdeck, Card };
