import json
import requests
from sentence_transformers import SentenceTransformer
import chromadb
    # step-2 loop through the documents from a specific folder
    # step-3 for each doc, parse it.
    # step-4 taking 3 knowledge article docs,
    # I donot want to load every KB at once. 
    # instead I want to take a piece of it, load it in-mem, 
    # chunk it and convert into embeddings and clear the in-mem variables also
class KnowledgeAI:
    def __init__(self):
        self.chunks = None
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.PersistentClient(path='./chroma_store')
        self.collection = self.client.get_or_create_collection('policies')
        self.embedding = None
        self.doc_counter = 0
        
    def process_chunk(self, chunk_text, chunk_id):
        embeddings = self.model.encode(chunk_text)
        self.collection.add(
            documents=[chunk_text],
            embeddings=[embeddings.tolist()],
            ids = [chunk_id]
        )
        print()
    
    def loop_folder(self):
        #TODO: this function should actually iterate for the policy documents and then call the chunk document 
        #which chunks each document in paragraphs 
        folder = ''
        for doc in folder:
            print('')
             
    def chunk_document_by_paragraph(self):
        buffer = []
        paras = []
        with open('Documents/bronze.txt', 'r', encoding='utf-8') as document:
            for line in document: #loop through the every line
                strippedLine = line.strip() #trim every line to ensure it has content
                if strippedLine == "": #if 2 \n\n meaning end of para?
                    #instead of checking strippedLine for empty? if this is empty we have hit the end of a para
                    if buffer: #we pretty much have value if we read lines earlier so we get in
                        print('inside buffer if')
                        # Preserve the original formatting when making a chunk.
                        # if this is first para? do we even need to consider this for now?
                        #take last 2 elements of the buffer 
                        # which is last 2 lines of the para and attach it into chunk's end
                        # i think doing this is a good starting point to have overlap
                        #overlap = buffer[-2:]
                        #print(f'overlap', overlap)
                        if not len(paras) > 0: #this is valid only for the very first para we read from the file
                            chunk = '\n'.join(buffer) #.join(overlap)
                            self.process_chunk(chunk, f"doc_{self.doc_counter}")
                            self.doc_counter += 1
                            paras.append(buffer) #this saves all paras as single lines, again? then why do the above then?
                            print(paras)
                            #here we do not need to reset paras as this is the first one we saw and we need it 
                            buffer = []
                        else:
                            #read paras last element's last 2 values/elements
                            previousPara = paras[-1]
                            prevLast2lines = previousPara[-2:]
                            chunk = '\n'.join(prevLast2lines)
                            #chunk += '\n'.join(buffer)
                            chunk += '\n' + '\n'.join(buffer)
                            #chunk+='\n'.join().join(prevLast2lines)
                            print('last 2 lines: ', prevLast2lines)
                            print('previous para: ', previousPara)
                            print('appended chunk: ', chunk)
                            self.process_chunk(chunk, f"doc_{self.doc_counter}")
                            self.doc_counter += 1
                            #we add the curr buffer at the end so that above overlap is set. 
                            # else curr buffer would become the last element and splice becomes complex code
                            #efficiency - reset paras also as we need only 1 previous one for overlap creation.
                            paras = []
                            paras.append(buffer)
                            buffer = []
                            #this chunk is the one that handles the overlap to ensure continuity
                        #if len(paras) > 0:
                            #i have at least 1 para already read from the file.
                            #now take the last 2 lines from the para which is paras of [current para - 1 ]
                            # curr para data is in buffer
                            #so now chunk becomes buffer + paras last element's last 2 values/elements
                        
                        #embedding = self.model.encode(chunk) # chunk is encoded per para
                        # encode the chunk to vector array
                        # now where is my overlap? and then add to collection the chunk with overlap
                        # if we choose to overlap a para to para its going to be huge chunk
                        #though the inference is going to be good.
                        #can we not overlap last 2 sentences of a para with a new one?
                        #what if each para is a pretty long single line with on `\n` but with a period
                        #save to chromaDB the embedding
                        #print('*****: ', line)        
                        #print('#####: ', chunk)
                        #buffer = []
                        #print('&&&&&: ', embedding)
                        
                else:
                    buffer.append(strippedLine)
        
        # Handle the final paragraph if file doesn't end with empty lines
        if buffer:
            print('Processing final paragraph')
            if not paras:  # If this is the only paragraph
                chunk = '\n'.join(buffer)
                self.process_chunk(chunk, f"doc_{self.doc_counter}")
            else:
                # Apply overlap with previous paragraph
                previousPara = paras[-1]
                prevLast2lines = previousPara[-2:] if len(previousPara) >= 2 else previousPara
                chunk = '\n'.join(prevLast2lines) + '\n' + '\n'.join(buffer)
                self.process_chunk(chunk, f"doc_{self.doc_counter}")
            
            self.doc_counter += 1
            paras.append(buffer)
        
        print(f"Total chunks processed: {self.doc_counter}")
        print(f"Total paragraphs found: {len(paras)}")
        
    
    def interactive_mode(self):
        print('inside interactive_mode:')
        while True:
            question = input("\n🔍 Ask a question (or type 'exit'): ")
            if question.lower() in ["exit", "quit"]:
                break
            context = self.user_query(question)
            prompt = f"Use the following context to answer the question.\n\nContext:\n{context}\n\nQuestion: {question}"
            answer = self.prompt_llm("You are a policy helper agent.", prompt)
            print("\n🤖 Answer:\n", answer)
                       
    def user_query(self, question, n_results = 5):
        print('user question', question)
        print('inside query: ', question)
        query_embedding = self.model.encode([question]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )
        top_chunks = results["documents"][0]
        print('inside top_chunks: ', top_chunks)
        return "\n\n".join(top_chunks)
        
        
    
    
    def prompt_llm(self, system_prompt, user_prompt, model_name="phi:latest"):
        print('inside query_ollama: ', model_name)
        url = "http://localhost:11434/api/chat"
        
        updated_system_prompt = f"""{system_prompt}
        - IMPORTANT INSTRUCTIONS
        - Be precise with currency amounts and percentages from tables
        """
        
        response = requests.post(url, json={
            "model": model_name,
            "messages": [
                {"role": "system", "content": updated_system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        })
        response.raise_for_status()
        print('response for query_ollama: ', response)
        print('Raw response text:', response.text)
        answer_parts = []
        for line in response.text.strip().splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                content = data.get("message", {}).get("content", "")
                answer_parts.append(content)
                print('*****: ', content)
                if data.get("done", False):
                    break
            except json.JSONDecodeError:
                # If any line is malformed, you can skip or log
                pass

        full_answer = "".join(answer_parts).strip()
        return full_answer     

kb = KnowledgeAI()

kb.chunk_document_by_paragraph()
kb.interactive_mode()
print('finished creating embeddings')