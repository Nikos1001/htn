import { AppProps } from 'next/app';
import Head from 'next/head';
import { MantineProvider } from '@mantine/core';
import './global.css';
import { Image } from '@mantine/core';

export default function App(props: AppProps) {
  const { Component, pageProps } = props;

  return (
    <>
      <Head>
        <title>Cardsmart</title>
        <meta name="viewport" content="minimum-scale=1, initial-scale=1, width=device-width" />
      </Head>

      <MantineProvider
        withGlobalStyles
        withNormalizeCSS
        theme={{
          colorScheme: 'dark',
        }}
      >
        <Image style={{opacity: '0.1', position: 'fixed', top: '-10vh', left: '-10vw', width: '120vw', height: '120vh', userSelect: 'none', pointerEvents: 'none'}} src={'./goo.png'}/>
        <Component {...pageProps} />
      </MantineProvider>
    </>
  );
}