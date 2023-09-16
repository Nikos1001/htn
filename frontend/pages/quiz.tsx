'use client';

import { Flex, Textarea, Title, Button, Loader } from "@mantine/core";
import { Flashdeck, apiRootURL, post } from '../common'
import { useEffect, useState } from "react";
import { useRouter } from "next/router";
import confetti from 'canvas-confetti'; 

type QuizState = 'generating' | 'quiz' | 'result';
type FeedbackState = 'input' | 'generating' | 'done';

export default function Quiz() {
    const [quizState, setQuizState] = useState<QuizState>('generating');
    const [questions, setQuestions] = useState<string[] | null>(null);
    const [currQuestion, setCurrQuestion] = useState(0);
    const [feedback, setFeedback] = useState<string | null>(null);
    const [feedbackState, setFeedbackState] = useState<FeedbackState>('input');
    const [deck, setDeck] = useState<Flashdeck | null>(null);
    const [answer, setAnswer] = useState('');
    const [score, setScore] = useState(0);
    const router = useRouter();

    const buttonGradient = {from: 'teal', to: 'lime', deg: 105};

    console.log(questions);

    useEffect(() => {
        let deckData = JSON.parse(localStorage.getItem('deck') as string);
        post(apiRootURL + '/question', {text: deckData?.text, title: deckData?.title}).then(questions => {
            setQuestions(questions);
            setQuizState('quiz');
        });
        setDeck(deckData);
    }, []);

    const getFeedbackUI = () => {
        switch(feedbackState) {
            case 'input':
                return <Button variant='gradient' gradient={buttonGradient} onClick={() => {
                        setFeedbackState('generating');
                        post(apiRootURL + '/answer', {
                            text: deck?.text,
                            question: questions ? questions[currQuestion] : '',
                            answer: answer
                        }).then(feedback => {
                            setFeedbackState('done');
                            setFeedback(feedback.feedback);
                            const lower = feedback.feedback.toLowerCase();
                            const correct = lower.includes('correct') && !lower.includes('not correct') && !lower.includes('incorrect');
                            if(correct) {
                                setScore(score + 1);
                                confetti({
                                    particleCount: 100,
                                    spread: 70,
                                    origin: { y: 0.6 }
                                });
                            }
                        })
                    }}>Submit</Button>;
            case 'generating':
                return <Loader color="lime" variant="bars"/>;
            case 'done':
                return <>
                    {feedback}
                    <Button style={{marginTop: '50px'}} variant='gradient' gradient={buttonGradient} onClick={() => {
                        if(questions && currQuestion + 1 < questions.length) {
                            setCurrQuestion(currQuestion + 1);
                            setFeedbackState('input');
                        } else {
                            setQuizState('result');
                            confetti({
                                particleCount: 100,
                                spread: 70,
                                origin: { y: 0.6 }
                            });
                        }
                        setAnswer('');
                    }}>{(questions && currQuestion + 1 < questions?.length) ? 'Next Question' : 'Finish'}</Button>
                </>;
        }
    }

    const getUI = () => {
        switch(quizState) {
            case 'generating':
                return <>
                    <Title size='h2' style={{marginBottom: '50px'}}>Generating Quiz...</Title>
                    <Loader color="lime" variant="bars"/>
                </>;
            case 'quiz':
                return <>
                    <Title size='h2' style={{marginBottom: '50px'}}>{questions ? questions[currQuestion] : ''}</Title>
                    <Textarea value={answer} onChange={(e) => setAnswer(e.currentTarget.value)} style={{marginBottom: '40px', width: '800px'}} minRows={5} placeholder='Answer'/>
                    {getFeedbackUI()}
                </>;
            case 'result':
                return <>
                    <Title size='h2' style={{marginBottom: '50px'}}>Score: {score} / {questions?.length}</Title>
                    <Button variant='gradient' gradient={buttonGradient} onClick={() => 
                        router.push('/')
                    }>Return to Flashdecks</Button>
                </>;
        }
    };

    return <Flex justify='center' align='center' direction='column' style={{position: 'absolute', top: '0', left: '0', width: '100vw', height: '100vh'}}>
        {getUI()}
    </Flex>;

}