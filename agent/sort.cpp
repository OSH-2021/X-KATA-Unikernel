#include<iostream>
#include<stdlib.h>
#include<time.h>

/*void read(char* filename, int* p) {
	FILE* fp;
	fp = fopen(filename, "r");
	if (fp == NULL) {
		printf("无法读取文件！\n");
		return;
	}
	int length;
	fscanf(fp,"%d\n",&length);
	for (int i = 0;i < 100000;i++)
		fscanf(fp, "%d", &p[i]);
	fclose(fp);
}

void write(char* filename, int *p) {
	FILE* fp;
	fp = fopen(filename, "w");
	if (fp == NULL) {
		printf("无法写入文件！\n");
		return;
	}
	for (int i = 0;i < 100000;i++)
		fprintf(fp, "%d ", p[i]);
	fclose(fp);
}*/

int partition(int *A,int p,int r) {
	//划分数组
	int x = A[r];//固定划分元
	int i = p - 1;
	int t;
	for(int j=p;j<r;j++)
		//遍历数组
		if (A[j] <= x) {
			//当访问元素小于等于划分元时，将该元素与i位置元素交换，i右移
			i++;
			t = A[i];
			A[i] = A[j];
			A[j] = t;
		}
	//将(i+1)位置元素与划分元交换
	t = A[i + 1];
	A[i + 1] = A[r];
	A[r] = t;
	return i + 1;//返回划分元下标
}

void InsertionSort(int* A, int p, int r) {
	//插入排序
	int key, i;
	for (int j = p + 1;j <= r;j++) {
		key = A[j];
		i = j - 1;
		while (i>=0 && A[i] > key) {
			A[i + 1] = A[i];
			i--;
			A[i + 1] = key;
		}
	}
}

int main() {
    srand(time(NULL));
    time_t start, end;
	int A[100000];
	for(int i=0;i<100000;i++)
		A[i]=rand()%100000;

	start = clock();
	InsertionSort(A, 0, 99999);
	end = clock();
	double consume = double(end - start)/CLOCKS_PER_SEC;
	std::cout<<"sort completed"<<std::endl;
	std::cout<<"time consume: "<<consume<<'s'<<std::endl;
	while(1);
}
