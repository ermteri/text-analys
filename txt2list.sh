#!/bin/bash

# Läs stdin
input=$(cat)

# Ersätt radbrytningar, kommatecken och mellanslag med radbrytning
words=$(echo "$input" | tr ', ' '\n')

# Filtrera bort tomma rader
words=$(echo "$words" | sed '/^$/d')

# Bygg Python-lista
printf "["
first=true
while read -r word; do
    if [ "$first" = true ]; then
        first=false
    else
        printf ", "
    fi
    printf "\"%s\"" "$word"
done <<< "$words"
printf "]\n"

