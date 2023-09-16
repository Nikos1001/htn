'use client';

import { Flex, Textarea, Title, Button } from "@mantine/core";
import { Flashdeck, apiRootURL, post } from '../common'
import { useEffect, useState } from "react";

export default function Quiz() {
    const buttonGradient = {from: 'teal', to: 'lime', deg: 105};

    useEffect(() => {
        const deck = JSON.parse(localStorage.getItem('deck') as string);
        post(apiRootURL + '/question', {text: deck?.text});
    }, []);

    return <Flex justify='center' align='center' direction='column' style={{position: 'absolute', top: '0', left: '0', width: '100vw', height: '100vh'}}>
        <Title size='h2' style={{marginBottom: '50px'}}>What is the meaning of life?</Title>
        <Textarea style={{marginBottom: '40px', width: '800px'}} minRows={5} placeholder='Answer'/>
        <Button variant='gradient' gradient={buttonGradient}>Submit</Button>
    </Flex>;

}