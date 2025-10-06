/* 
    CH-230-A 
    a4_p12.c
    Denis Rosu
    DROSU@constructor.university
*/
#include <stdio.h>
#include <string.h>

/*funtion to replace all characters c with the character e in a string*/
void replace_ALL(char *str, char c, char e){
    int i;
    for(i=0; str[i] != '\0'; i++){
        if (str[i]==c)
            str[i]=e;
    }
}

int main () {
    char str[50], c, e;
    while (1){ //infinit loop
        printf("Enter string: ");
        fgets(str,sizeof(str),stdin);
        str[strcspn(str, "\n")] = '\0';
        if (strcmp(str,"stop")==0)
            break;
        /*breaking the roop when we type stop*/
        printf("Enter character to be replaced = ");
        scanf(" %c",&c);
        printf("Enter replacing character = ");
        scanf(" %c",&e);
        while (getchar() != '\n');
        /*getting rid of garbage variables*/
        replace_ALL(str, c, e);
        printf("New string: %s\n",str);
    }
    return 0;
}