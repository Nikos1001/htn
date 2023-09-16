
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

const apiRootURL = 'http://127.0.0.1:8080';

export { get, post, apiRootURL };
export type { Flashdeck, Card };
