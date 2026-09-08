# **E-Commerce Order Fulfillment Analysis**  

## **Project Overview**  
This project analyzes the **order fulfillment process** of an e-commerce business, covering **sales trends, product performance, customer segmentation, shipping cost optimization, and payment method analysis**.  

Using **Advanced SQL Techniques** and **Python-based data visualization**, we extract insights to help businesses **improve logistics, boost sales, and enhance customer satisfaction**.  

---

## **Objectives**  
1**Optimize order processing efficiency** – Track delays and enhance fulfillment times.  
2 **Identify top-selling products** – Understand which products generate the highest revenue.  
3 **Segment high-value customers** – Analyze customer spending behavior and engagement.  
4 **Reduce shipping costs** – Evaluate cost variations based on order priority.  
5 **Identify preferred payment methods** – Determine customer payment preferences for better financial strategies.  

---

## **Dataset Overview**  
- **Source**: E-Commerce transaction records with **51,290 rows** and **16 columns**  
- **Data Transformation**: The raw dataset was **normalized into four tables** for efficient querying:
  - `Orders` – Order details, including sales, profit, and shipping costs.  
  - `Customers` – Customer demographics such as gender, login type, and device.  
  - `Products` – List of all products and their categories.  
  - `Categories` – Broader classification of product types.  

---

## **Advanced SQL Techniques Used**  
This project incorporates **Advanced SQL Techniques** to improve query performance, simplify analysis, and generate powerful insights:  

### **1️ Window Functions**  
   - Used to **rank top-selling products** and **calculate cumulative sales over time**.  
   - Helps in **understanding product demand trends dynamically**.  

### **2️ Common Table Expressions (CTEs)**  
   - Simplifies **customer segmentation analysis** by organizing complex queries.  
   - Enhances readability and maintains **modular query execution**.  

### **3️ Ranking Functions (RANK() OVER)**  
   - Assigns rankings to products based on total sales.  
   - Useful for **identifying best-performing items efficiently**.  

### **4️ Partitioning & Indexing for Performance Optimization**  
   - Used for **query optimization**, especially for large datasets.  
   - Ensures **faster retrieval of insights** from orders and customer data.  

---

##  **Business Insights & Findings**  

### ** Sales & Revenue Analysis**  
- The business generated **$7.8M in total sales**, with a **$3.6M profit margin**.  
- **Sales peaked in May and November**, indicating strong **seasonal demand trends**.  

### ** Top-Selling Products**  
- The **highest-selling categories were Fashion and Footwear**, with **T-Shirts, Watches, and Running Shoes leading sales**.  
- **Bundling slower-moving items with high-performing products** could increase sales.  

### ** Customer Segmentation & Retention**  
- **High-spending customers are primarily male**, highlighting an opportunity for **targeted promotions**.  
- A **VIP loyalty program** can enhance customer retention and **increase repeat purchases**.  

### ** Order Fulfillment & Shipping Cost Optimization**  
- **High-priority orders have significantly higher shipping costs**.  
- Encouraging **bulk orders and standard delivery options** can help reduce logistics expenses.  

### ** Payment Method Preferences**  
- **Credit cards dominate transactions (74% of total revenue)**, while **e-wallet adoption remains low**.  
- **Promoting digital payment incentives** can increase checkout conversion rates.  

---

##  **Business Recommendations**  
 **Optimize Order Processing Efficiency**  
   - Implement **automation in warehouses** to reduce the average processing time (currently 5.25 days).  
   - Introduce **real-time order tracking** to enhance transparency and customer trust.  

 **Increase Revenue with Targeted Promotions**  
   - Leverage **seasonal sales trends** by launching exclusive discounts during peak months.  
   - Promote **high-ranking products (T-Shirts, Watches, and Shoes)** through advertising.  

 **Improve Customer Retention Strategies**  
   - Create **personalized offers for repeat customers** based on purchase history.  
   - Implement a **loyalty program** to encourage repeat spending.  

 **Reduce Shipping Costs Without Affecting Delivery Time**  
   - Offer **free standard shipping for bulk orders** to reduce per-item logistics costs.  
   - Optimize **partnerships with shipping carriers** for discounted high-priority shipping rates.  

 **Enhance Payment Flexibility & Checkout Experience**  
   - Encourage **e-wallet and debit card transactions** by offering cashback incentives.  
   - Introduce **Buy Now, Pay Later (BNPL) options** to reduce cart abandonment.  

---

##  **Technologies Used**  
- **Database**: SQLite  
- **Query Language**: SQL  
- **Data Processing**: Pandas  
- **Visualization**: Matplotlib, Seaborn  
- **Development Environment**: Jupyter Notebook  

---

##  **Project Files & Repository Structure**  
 `Ecommerce_SQL_DATAProject.db` – SQLite database file  
 `ecommerce_schema.sql` – Collection of SQL scripts used in analysis  
 `E_Commerce_Analysis_using_Advanced_SQL.ipynb` – Jupyter Notebook for SQL execution & visualization    
 `README.md` – Documentation for project overview and findings  

---
